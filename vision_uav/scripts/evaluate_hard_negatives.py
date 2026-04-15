#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from common import load_yaml, resolve_workspace_path
from infer_video import run_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run inference on hard-negative videos or image folders and summarize false positives."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/eval_hard_negatives_template.yaml",
        help="Path to the hard-negative evaluation YAML config.",
    )
    parser.add_argument("--model", default=None, help="Optional explicit model override.")
    parser.add_argument("--source", default=None, help="Optional explicit source override.")
    parser.add_argument("--source-id", default=None, help="Optional explicit source_id override.")
    parser.add_argument("--name", default=None, help="Optional explicit output name override.")
    parser.add_argument("--project", default=None, help="Optional explicit output project override.")
    return parser.parse_args()


def load_predictions(jsonl_path: Path) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            frames.append(json.loads(line))
    return frames


def frame_row(frame: dict[str, Any]) -> dict[str, Any]:
    detections = frame.get("detections", [])
    confidences = [float(item["confidence"]) for item in detections]
    classes = [str(item["class_name"]) for item in detections]
    return {
        "frame_id": int(frame["frame_id"]),
        "timestamp_ms": float(frame["timestamp_ms"]),
        "detection_count": len(detections),
        "max_confidence": max(confidences) if confidences else 0.0,
        "mean_confidence": mean(confidences) if confidences else 0.0,
        "classes": ",".join(classes),
    }


def build_summary(
    frames: list[dict[str, Any]],
    source_id: str,
    high_confidence_threshold: float,
    top_k_frames: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = [frame_row(frame) for frame in frames]
    total_frames = len(rows)
    frames_with_detections = [row for row in rows if row["detection_count"] > 0]
    high_conf_frames = [row for row in rows if row["max_confidence"] >= high_confidence_threshold]
    total_detections = sum(int(row["detection_count"]) for row in rows)
    top_frames = sorted(rows, key=lambda row: (row["max_confidence"], row["detection_count"]), reverse=True)[:top_k_frames]

    summary = {
        "source_id": source_id,
        "assumption": "all detections on this source are treated as false positives",
        "total_frames": total_frames,
        "frames_with_detections": len(frames_with_detections),
        "frames_without_detections": total_frames - len(frames_with_detections),
        "frame_false_positive_rate": round(len(frames_with_detections) / total_frames, 6) if total_frames else 0.0,
        "total_detections": total_detections,
        "mean_detections_per_frame": round(total_detections / total_frames, 6) if total_frames else 0.0,
        "mean_detections_on_positive_frames": round(
            total_detections / len(frames_with_detections), 6
        )
        if frames_with_detections
        else 0.0,
        "max_confidence": round(max((row["max_confidence"] for row in rows), default=0.0), 6),
        "mean_confidence_on_positive_frames": round(
            mean(row["mean_confidence"] for row in frames_with_detections), 6
        )
        if frames_with_detections
        else 0.0,
        "high_confidence_threshold": high_confidence_threshold,
        "frames_at_or_above_threshold": len(high_conf_frames),
        "top_k_frames": top_k_frames,
    }
    return summary, top_frames


def write_frame_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = ["frame_id", "timestamp_ms", "detection_count", "max_confidence", "mean_confidence", "classes"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    high_confidence_threshold = float(config.get("high_confidence_threshold", 0.5))
    top_k_frames = int(config.get("top_k_frames", 20))

    result = run_inference(
        args.config,
        model_override=args.model,
        source_override=args.source,
        source_id_override=args.source_id,
        name_override=args.name,
        project_override=args.project,
    )

    predictions_path = Path(result["predictions_jsonl"])
    output_root = Path(result["output_root"])
    frames = load_predictions(predictions_path)
    rows = [frame_row(frame) for frame in frames]
    summary, top_frames = build_summary(frames, str(result["source_id"]), high_confidence_threshold, top_k_frames)

    summary_path = output_root / "false_positive_summary.json"
    top_frames_path = output_root / "top_false_positive_frames.json"
    frame_csv_path = output_root / "frame_detections.csv"

    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    top_frames_path.write_text(json.dumps(top_frames, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_frame_csv(frame_csv_path, rows)

    print(f"output_root={output_root}")
    print(f"overlay_mp4={output_root / 'overlay.mp4'}")
    print(f"predictions_jsonl={predictions_path}")
    print(f"summary_json={summary_path}")
    print(f"top_false_positive_frames={top_frames_path}")
    print(f"frame_detections_csv={frame_csv_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
