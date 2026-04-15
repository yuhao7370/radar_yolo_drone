#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import cv2

from common import ensure_dir, load_yaml, load_yolo_model, resolve_workspace_path
from infer_video import detections_from_result


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mine false-positive hard negatives from bird, sky and clutter candidate sources."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/hard_negative_round2_mining.yaml",
        help="Path to the hard-negative mining YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def dhash(image) -> int:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bit)
    return value


def hamming_distance(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def is_near_duplicate(existing_hashes: list[int], candidate_hash: int, threshold: int) -> bool:
    return any(hamming_distance(item, candidate_hash) <= threshold for item in existing_hashes)


def iter_image_files(path: Path) -> list[Path]:
    return sorted(
        file_path for file_path in path.iterdir()
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_SUFFIXES
    )


def process_image_dir(
    model,
    source_name: str,
    category: str,
    source_dir: Path,
    output_dir: Path,
    conf: float,
    imgsz: int,
    device: int | str,
    hash_threshold: int,
    existing_hashes: list[int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mined_rows: list[dict[str, Any]] = []
    examined = 0
    detected = 0
    duplicate_skipped = 0
    for image_path in iter_image_files(source_dir):
        frame = cv2.imread(str(image_path))
        if frame is None:
            continue
        examined += 1
        result = model.predict(source=frame, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
        detections = detections_from_result(result)
        if not detections:
            continue
        detected += 1
        image_hash = dhash(frame)
        if is_near_duplicate(existing_hashes, image_hash, hash_threshold):
            duplicate_skipped += 1
            continue
        existing_hashes.append(image_hash)
        destination_name = f"{source_name}_{image_path.name}"
        destination_path = output_dir / destination_name
        if not destination_path.exists():
            shutil.copy2(image_path, destination_path)
        mined_rows.append(
            {
                "category": category,
                "source_name": source_name,
                "source_type": "image_dir",
                "source_path": str(image_path),
                "saved_path": str(destination_path),
                "max_confidence": max(float(item["confidence"]) for item in detections),
                "detection_count": len(detections),
            }
        )
    stats = {
        "source_name": source_name,
        "source_type": "image_dir",
        "examined_frames": examined,
        "detected_frames": detected,
        "saved_frames": len(mined_rows),
        "duplicate_skipped": duplicate_skipped,
    }
    return mined_rows, stats


def process_video_dir(
    model,
    source_name: str,
    category: str,
    source_dir: Path,
    output_dir: Path,
    conf: float,
    imgsz: int,
    device: int | str,
    hash_threshold: int,
    min_gap_frames: int,
    existing_hashes: list[int],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    mined_rows: list[dict[str, Any]] = []
    examined = 0
    detected = 0
    duplicate_skipped = 0

    for video_path in sorted(source_dir.glob("*.mp4")):
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        frame_idx = 0
        last_saved_frame_idx = -min_gap_frames
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                examined += 1
                result = model.predict(source=frame, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
                detections = detections_from_result(result)
                if not detections:
                    frame_idx += 1
                    continue
                detected += 1
                if frame_idx - last_saved_frame_idx < min_gap_frames:
                    frame_idx += 1
                    continue
                image_hash = dhash(frame)
                if is_near_duplicate(existing_hashes, image_hash, hash_threshold):
                    duplicate_skipped += 1
                    frame_idx += 1
                    continue
                existing_hashes.append(image_hash)
                last_saved_frame_idx = frame_idx
                destination_name = f"{source_name}_{video_path.stem}_{frame_idx:06d}.jpg"
                destination_path = output_dir / destination_name
                if not destination_path.exists():
                    if not cv2.imwrite(str(destination_path), frame):
                        raise RuntimeError(f"Failed to save mined frame: {destination_path}")
                mined_rows.append(
                    {
                        "category": category,
                        "source_name": source_name,
                        "source_type": "video_dir",
                        "source_path": str(video_path),
                        "saved_path": str(destination_path),
                        "frame_idx": frame_idx,
                        "max_confidence": max(float(item["confidence"]) for item in detections),
                        "detection_count": len(detections),
                    }
                )
                frame_idx += 1
        finally:
            capture.release()

    stats = {
        "source_name": source_name,
        "source_type": "video_dir",
        "examined_frames": examined,
        "detected_frames": detected,
        "saved_frames": len(mined_rows),
        "duplicate_skipped": duplicate_skipped,
    }
    return mined_rows, stats


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    weights = args.weights or str(config["weights"])
    fallback_model = config.get("fallback_model")
    model = load_yolo_model(weights, str(fallback_model) if fallback_model else None)

    output_root = ensure_dir(resolve_workspace_path(config["project"])) / str(config["name"])
    ensure_dir(output_root)

    conf = float(config["conf"])
    imgsz = int(config["imgsz"])
    device = config.get("device", 0)
    min_gap_frames = int(config["video_min_gap_frames"])
    hash_threshold = int(config["image_hash_hamming_threshold"])

    by_category: dict[str, list[dict[str, Any]]] = {"bird": [], "pure_sky": [], "clutter": []}
    source_stats: list[dict[str, Any]] = []
    hashes_by_category: dict[str, list[int]] = {"bird": [], "pure_sky": [], "clutter": []}

    for source_cfg in config["sources"]:
        category = str(source_cfg["category"])
        source_name = str(source_cfg["source_name"])
        source_type = str(source_cfg["source_type"])
        source_path = resolve_workspace_path(source_cfg["source"])
        category_output = ensure_dir(output_root / category)

        if source_type == "image_dir":
            rows, stats = process_image_dir(
                model,
                source_name,
                category,
                source_path,
                category_output,
                conf,
                imgsz,
                device,
                hash_threshold,
                hashes_by_category[category],
            )
        elif source_type == "video_dir":
            rows, stats = process_video_dir(
                model,
                source_name,
                category,
                source_path,
                category_output,
                conf,
                imgsz,
                device,
                hash_threshold,
                min_gap_frames,
                hashes_by_category[category],
            )
        else:
            raise ValueError(f"Unsupported source_type: {source_type}")

        by_category[category].extend(rows)
        source_stats.append(stats)

    quotas = {key: int(value) for key, value in config["quotas"].items()}
    selected_by_category: dict[str, list[dict[str, Any]]] = {}
    category_summary: dict[str, dict[str, Any]] = {}
    for category, rows in by_category.items():
        rows.sort(key=lambda row: float(row["max_confidence"]), reverse=True)
        selected = rows[: quotas.get(category, len(rows))]
        selected_by_category[category] = selected
        category_summary[category] = {
            "target_quota": quotas.get(category, 0),
            "available_mined": len(rows),
            "selected_for_hn_v2": len(selected),
            "quota_shortfall": max(0, quotas.get(category, 0) - len(selected)),
        }

    summary = {
        "weights": str(resolve_workspace_path(weights)),
        "config": str(resolve_workspace_path(args.config)),
        "source_stats": source_stats,
        "category_summary": category_summary,
    }
    (output_root / "mining_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for category, rows in selected_by_category.items():
        (output_root / f"{category}_selected.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    print(f"output_root={output_root}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
