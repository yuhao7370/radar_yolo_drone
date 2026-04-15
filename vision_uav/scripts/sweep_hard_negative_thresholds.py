#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2

from common import ensure_dir, extract_detection_metrics, load_yaml, load_yolo_model, resolve_workspace_path
from evaluate import resolve_eval_args
from infer_video import IMAGE_SUFFIXES, iter_image_paths

VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@dataclass
class SourceConfig:
    source: Path
    source_id: str
    fps: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sweep confidence thresholds on hard-negative sources and recommend a threshold."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/hard_negative_threshold_sweep.yaml",
        help="Path to the threshold sweep YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def summarize_source(model, source_cfg: SourceConfig, conf: float, imgsz: int, device: int | str) -> dict[str, Any]:
    total_frames = 0
    frames_with_detections = 0
    total_detections = 0
    max_confidence = 0.0

    source = source_cfg.source
    if source.is_dir():
        image_paths = iter_image_paths(source)
        if image_paths:
            frame_iter = (
                (frame_id, (frame_id / source_cfg.fps) * 1000.0, cv2.imread(str(image_path)))
                for frame_id, image_path in enumerate(image_paths)
            )
        else:
            video_paths = sorted(
                path for path in source.iterdir()
                if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
            )
            if not video_paths:
                raise ValueError(f"No supported image or video files found under {source}")

            def _video_dir_iter():
                frame_id = 0
                for video_path in video_paths:
                    capture = cv2.VideoCapture(str(video_path))
                    if not capture.isOpened():
                        raise RuntimeError(f"Failed to open source video: {video_path}")
                    try:
                        while True:
                            ok, frame = capture.read()
                            if not ok:
                                break
                            yield frame_id, float(frame_id / source_cfg.fps * 1000.0), frame
                            frame_id += 1
                    finally:
                        capture.release()

            frame_iter = _video_dir_iter()
    else:
        capture = cv2.VideoCapture(str(source))
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open source video: {source}")

        def _video_iter():
            frame_id = 0
            try:
                while True:
                    ok, frame = capture.read()
                    if not ok:
                        break
                    yield frame_id, float(capture.get(cv2.CAP_PROP_POS_MSEC)), frame
                    frame_id += 1
            finally:
                capture.release()

        frame_iter = _video_iter()

    for frame_id, timestamp_ms, frame in frame_iter:
        if frame is None:
            raise RuntimeError(f"Failed to read frame for source {source_cfg.source_id}")
        result = model.predict(source=frame, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
        boxes = getattr(result, "boxes", None)
        detections = 0 if boxes is None else int(len(boxes))
        total_frames += 1
        total_detections += detections
        if detections > 0:
            frames_with_detections += 1
            max_confidence = max(max_confidence, max(boxes.conf.cpu().tolist()))

    frame_fp_rate = frames_with_detections / total_frames if total_frames else 0.0
    return {
        "source_id": source_cfg.source_id,
        "source": str(source_cfg.source),
        "threshold": conf,
        "total_frames": total_frames,
        "frames_with_detections": frames_with_detections,
        "total_detections": total_detections,
        "frame_false_positive_rate": frame_fp_rate,
        "max_confidence": max_confidence,
        "mean_detections_per_frame": (total_detections / total_frames) if total_frames else 0.0,
    }


def aggregate_rows(rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    total_frames = sum(int(row["total_frames"]) for row in rows)
    frames_with_detections = sum(int(row["frames_with_detections"]) for row in rows)
    total_detections = sum(int(row["total_detections"]) for row in rows)
    return {
        "source_id": "__all__",
        "source": "aggregated",
        "threshold": threshold,
        "total_frames": total_frames,
        "frames_with_detections": frames_with_detections,
        "total_detections": total_detections,
        "frame_false_positive_rate": (frames_with_detections / total_frames) if total_frames else 0.0,
        "max_confidence": max((float(row["max_confidence"]) for row in rows), default=0.0),
        "mean_detections_per_frame": (total_detections / total_frames) if total_frames else 0.0,
    }


def evaluate_recall(model, config_path: Path, threshold: float) -> dict[str, Any]:
    config = load_yaml(config_path)
    eval_args = resolve_eval_args(config)
    eval_args["conf"] = threshold
    metrics = model.val(**eval_args)
    return extract_detection_metrics(metrics)


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
    default_fps = float(config.get("fps", 10.0))
    thresholds = [float(value) for value in config["thresholds"]]
    target_fp_rate = float(config.get("target_frame_false_positive_rate", 0.05))
    max_recall_drop = float(config.get("max_recall_drop", 0.03))
    baseline_val_recall = float(config.get("baseline_val_recall", 0.0))
    baseline_test_recall = float(config.get("baseline_test_recall", 0.0))

    sources = [
        SourceConfig(
            source=resolve_workspace_path(item["source"]),
            source_id=str(item["source_id"]),
            fps=float(item.get("fps", default_fps)),
        )
        for item in config["sources"]
    ]

    rows: list[dict[str, Any]] = []
    aggregate_rows_by_threshold: list[dict[str, Any]] = []

    for threshold in thresholds:
        source_rows = [
            summarize_source(model, source_cfg, threshold, imgsz, device)
            for source_cfg in sources
        ]
        rows.extend(source_rows)
        aggregate_rows_by_threshold.append(aggregate_rows(source_rows, threshold))

    threshold_csv = output_root / "threshold_sweep.csv"
    with threshold_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "source_id",
            "source",
            "threshold",
            "total_frames",
            "frames_with_detections",
            "total_detections",
            "frame_false_positive_rate",
            "max_confidence",
            "mean_detections_per_frame",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        writer.writerows(aggregate_rows_by_threshold)

    eligible = [
        row for row in aggregate_rows_by_threshold
        if float(row["frame_false_positive_rate"]) <= target_fp_rate
    ]

    recommendation: dict[str, Any] = {
        "weights": str(resolve_workspace_path(weights)),
        "target_frame_false_positive_rate": target_fp_rate,
        "max_recall_drop": max_recall_drop,
        "baseline_val_recall": baseline_val_recall,
        "baseline_test_recall": baseline_test_recall,
        "selected_threshold": None,
        "needs_hard_negative_retrain": False,
        "reason": "",
    }

    if not eligible:
        recommendation["needs_hard_negative_retrain"] = True
        recommendation["reason"] = "没有任何阈值满足 hard negative frame_false_positive_rate 约束。"
    else:
        selected = min(eligible, key=lambda row: float(row["threshold"]))
        selected_threshold = float(selected["threshold"])
        recommendation["selected_threshold"] = selected_threshold
        recommendation["hard_negative_summary"] = selected

        val_metrics = evaluate_recall(model, resolve_workspace_path(config["val_eval_config"]), selected_threshold)
        test_metrics = evaluate_recall(model, resolve_workspace_path(config["test_eval_config"]), selected_threshold)
        recommendation["val_metrics_at_selected_threshold"] = val_metrics
        recommendation["test_metrics_at_selected_threshold"] = test_metrics
        recommendation["val_recall_drop"] = baseline_val_recall - float(val_metrics["recall"])
        recommendation["test_recall_drop"] = baseline_test_recall - float(test_metrics["recall"])

        if (
            recommendation["val_recall_drop"] > max_recall_drop
            or recommendation["test_recall_drop"] > max_recall_drop
        ):
            recommendation["selected_threshold"] = None
            recommendation["needs_hard_negative_retrain"] = True
            recommendation["reason"] = "满足 hard negative 误检率约束的最低阈值会导致 val/test recall 下降超过限制。"
        else:
            recommendation["reason"] = "阈值搜索已满足 hard negative 误检率与 val/test recall 约束。"

    summary_path = output_root / "hard_negative_summary.json"
    summary_path.write_text(json.dumps(recommendation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"output_root={output_root}")
    print(f"threshold_sweep_csv={threshold_csv}")
    print(f"hard_negative_summary={summary_path}")
    print(json.dumps(recommendation, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
