#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import cv2

from common import ensure_dir, load_yaml, load_yolo_model, resolve_workspace_path
from infer_video import detections_from_result


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate multiple hard-negative suites and export threshold sweeps plus review tables."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/hard_negative_round2_baseline.yaml",
        help="Path to the hard-negative round2 evaluation YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def image_dir_from_manifest(manifest_path: Path, manifest: dict[str, Any]) -> Path:
    raw_dir = manifest.get("images_dir") or manifest.get("output_dir")
    if raw_dir is None:
        raise KeyError(f"Manifest does not define images_dir/output_dir: {manifest_path}")
    raw_dir_str = str(raw_dir)
    fallback_dir = manifest_path.parent / "images"
    if ":\\" in raw_dir_str or ":/" in raw_dir_str:
        if fallback_dir.exists():
            return fallback_dir
    image_dir = Path(str(raw_dir))
    if image_dir.exists():
        return image_dir
    if fallback_dir.exists():
        return fallback_dir
    raise FileNotFoundError(f"Cannot resolve suite image directory from manifest: {manifest_path}")


def run_suite_threshold(
    model,
    image_dir: Path,
    threshold: float,
    imgsz: int,
    device: int | str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    image_paths = sorted(
        path for path in image_dir.iterdir()
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )
    frame_rows: list[dict[str, Any]] = []
    frames_with_detections = 0
    total_detections = 0
    max_confidence = 0.0

    for frame_id, image_path in enumerate(image_paths):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise RuntimeError(f"Failed to read image: {image_path}")
        result = model.predict(source=frame, imgsz=imgsz, conf=threshold, device=device, verbose=False)[0]
        detections = detections_from_result(result)
        detection_count = len(detections)
        top_confidence = max((float(item["confidence"]) for item in detections), default=0.0)
        if detection_count > 0:
            frames_with_detections += 1
        total_detections += detection_count
        max_confidence = max(max_confidence, top_confidence)
        frame_rows.append(
            {
                "frame_id": frame_id,
                "image_name": image_path.name,
                "image_path": str(image_path),
                "detection_count": detection_count,
                "max_confidence": top_confidence,
                "detections": detections,
            }
        )

    total_frames = len(frame_rows)
    summary = {
        "threshold": threshold,
        "total_frames": total_frames,
        "frames_with_detections": frames_with_detections,
        "frames_without_detections": total_frames - frames_with_detections,
        "total_detections": total_detections,
        "frame_false_positive_rate": (frames_with_detections / total_frames) if total_frames else 0.0,
        "mean_detections_per_frame": (total_detections / total_frames) if total_frames else 0.0,
        "max_confidence": max_confidence,
    }
    return summary, frame_rows


def write_threshold_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "threshold",
                "total_frames",
                "frames_with_detections",
                "frames_without_detections",
                "total_detections",
                "frame_false_positive_rate",
                "mean_detections_per_frame",
                "max_confidence",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def write_review_csv(
    path: Path,
    frame_rows: list[dict[str, Any]],
    suggested_taxonomy: str,
) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "frame_id",
                "image_name",
                "image_path",
                "detection_count",
                "max_confidence",
                "suggested_taxonomy",
                "manual_taxonomy",
                "notes",
            ],
        )
        writer.writeheader()
        for row in frame_rows:
            writer.writerow(
                {
                    "frame_id": row["frame_id"],
                    "image_name": row["image_name"],
                    "image_path": row["image_path"],
                    "detection_count": row["detection_count"],
                    "max_confidence": f"{row['max_confidence']:.6f}",
                    "suggested_taxonomy": suggested_taxonomy if row["detection_count"] > 0 else "",
                    "manual_taxonomy": "",
                    "notes": "",
                }
            )


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    weights = args.weights or str(config["weights"])
    fallback_model = config.get("fallback_model")
    model = load_yolo_model(weights, str(fallback_model) if fallback_model else None)

    output_root = ensure_dir(resolve_workspace_path(config["project"])) / str(config["name"])
    ensure_dir(output_root)
    imgsz = int(config.get("imgsz", 960))
    device = config.get("device", 0)
    thresholds = [float(value) for value in config["thresholds"]]
    review_threshold = float(config["review_threshold"])
    top_k_frames = int(config.get("top_k_frames", 50))

    round_summary: list[dict[str, Any]] = []
    for suite_config in config["suites"]:
        suite_name = str(suite_config["suite_name"])
        suite_dir = ensure_dir(output_root / suite_name)
        manifest = load_manifest(resolve_workspace_path(suite_config["manifest"]))
        image_dir = image_dir_from_manifest(resolve_workspace_path(suite_config["manifest"]), manifest)
        suggested_taxonomy = str(suite_config["suggested_taxonomy"])
        target_fp_rate = float(suite_config["target_frame_false_positive_rate"])

        threshold_rows: list[dict[str, Any]] = []
        review_rows: list[dict[str, Any]] = []

        for threshold in thresholds:
            threshold_summary, frame_rows = run_suite_threshold(model, image_dir, threshold, imgsz, device)
            threshold_rows.append(threshold_summary)
            if abs(threshold - review_threshold) < 1e-9:
                review_rows = frame_rows

        threshold_csv_path = suite_dir / "threshold_sweep.csv"
        write_threshold_csv(threshold_csv_path, threshold_rows)

        top_frames = sorted(
            [row for row in review_rows if row["detection_count"] > 0],
            key=lambda row: (row["max_confidence"], row["detection_count"]),
            reverse=True,
        )[:top_k_frames]

        frame_detections_path = suite_dir / "frame_detections.csv"
        write_review_csv(frame_detections_path, review_rows, suggested_taxonomy)

        taxonomy_path = suite_dir / "fp_taxonomy.csv"
        write_review_csv(taxonomy_path, top_frames, suggested_taxonomy)

        top_frames_path = suite_dir / "top_false_positive_frames.json"
        top_frames_path.write_text(json.dumps(top_frames, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        selected_threshold = None
        for row in threshold_rows:
            if float(row["frame_false_positive_rate"]) <= target_fp_rate:
                selected_threshold = float(row["threshold"])
                break

        suite_summary = {
            "suite_name": suite_name,
            "target_frame_false_positive_rate": target_fp_rate,
            "review_threshold": review_threshold,
            "selected_threshold": selected_threshold,
            "top_k_frames": top_k_frames,
            "manifest_path": str(resolve_workspace_path(suite_config["manifest"])),
            "threshold_rows": threshold_rows,
            "review_positive_frames": len(top_frames),
            "note": "当前套件中的所有检测均视为 false positives。",
        }
        (suite_dir / "suite_summary.json").write_text(
            json.dumps(suite_summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        round_summary.append(
            {
                "suite_name": suite_name,
                "selected_threshold": selected_threshold,
                "review_threshold": review_threshold,
                "target_frame_false_positive_rate": target_fp_rate,
                "review_positive_frames": len(top_frames),
            }
        )

    (output_root / "round2_baseline_suite_summary.json").write_text(
        json.dumps(round_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_root={output_root}")
    print(f"suite_summary_json={output_root / 'round2_baseline_suite_summary.json'}")
    print(json.dumps(round_summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
