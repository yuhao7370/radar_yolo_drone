#!/usr/bin/env python
from __future__ import annotations

import argparse
import bisect
import csv
import json
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Offline decision-level fusion MVP.")
    parser.add_argument("--radar-jsonl", required=True, help="Path to radar_frames.jsonl")
    parser.add_argument("--vision-jsonl", required=True, help="Path to predictions.jsonl")
    parser.add_argument("--vision-overlay", required=True, help="Path to overlay.mp4")
    parser.add_argument("--output-dir", required=True, help="Fusion output directory")
    parser.add_argument("--vision-conf-threshold", type=float, default=0.45)
    parser.add_argument("--radar-score-threshold", type=float, default=0.60)
    parser.add_argument("--max-time-delta-ms", type=float, default=150.0)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def load_radar_score(image_path: Path) -> float:
    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Cannot read radar image: {image_path}")
    return float(image.max()) / 255.0


def nearest_radar_frame(radar_rows: list[dict], radar_timestamps: list[float], timestamp_ms: float) -> dict | None:
    idx = bisect.bisect_left(radar_timestamps, timestamp_ms)
    candidates = []
    if idx < len(radar_rows):
        candidates.append(radar_rows[idx])
    if idx > 0:
        candidates.append(radar_rows[idx - 1])
    if not candidates:
        return None
    return min(candidates, key=lambda row: abs(float(row["timestamp_ms"]) - timestamp_ms))


def classify_state(vision_positive: bool, radar_positive: bool) -> str:
    if vision_positive and radar_positive:
        return "agree_positive"
    if vision_positive and not radar_positive:
        return "vision_only"
    if not vision_positive and radar_positive:
        return "radar_only"
    return "agree_negative"


def render_demo_video(
    aligned_rows: list[dict],
    overlay_path: Path,
    radar_root: Path,
    output_path: Path,
) -> None:
    capture = cv2.VideoCapture(str(overlay_path))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open overlay video: {overlay_path}")

    fps = capture.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 20.0

    vision_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
    vision_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
    radar_panel_width = max(vision_height * 5 // 8, 640)
    canvas_width = vision_width + radar_panel_width
    canvas_height = vision_height

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (canvas_width, canvas_height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Cannot open fusion video writer: {output_path}")

    aligned_iter = iter(aligned_rows)
    current = next(aligned_iter, None)
    current_frame_id = 0

    while current is not None:
        ok, vision_frame = capture.read()
        if not ok:
            break
        if current_frame_id < int(current["vision_frame_id"]):
            current_frame_id += 1
            continue

        radar_img = cv2.imread(str(radar_root / current["radar_img_path"]), cv2.IMREAD_GRAYSCALE)
        if radar_img is None:
            raise FileNotFoundError(radar_root / current["radar_img_path"])
        radar_vis = cv2.applyColorMap(radar_img, cv2.COLORMAP_JET)
        radar_vis = cv2.resize(radar_vis, (radar_panel_width, canvas_height))

        canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        canvas[:, :vision_width] = vision_frame
        canvas[:, vision_width:] = radar_vis

        cv2.putText(canvas, f"vision frame: {current['vision_frame_id']}", (24, 48), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"radar frame: {current['radar_frame_id']}", (24, 92), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"dt={current['time_delta_ms']:.1f} ms", (24, 136), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"vision={current['vision_top_confidence']:.3f}", (24, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"radar={current['radar_score']:.3f}", (24, 224), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, current["state"], (24, 268), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 3, cv2.LINE_AA)
        cv2.putText(canvas, "Vision Overlay", (24, canvas_height - 24), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, "Radar Snapshot", (vision_width + 24, canvas_height - 24), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
        writer.write(canvas)

        current = next(aligned_iter, None)
        current_frame_id += 1

    capture.release()
    writer.release()


def main() -> None:
    args = parse_args()
    radar_jsonl = Path(args.radar_jsonl)
    vision_jsonl = Path(args.vision_jsonl)
    overlay_path = Path(args.vision_overlay)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    radar_rows = read_jsonl(radar_jsonl)
    vision_rows = read_jsonl(vision_jsonl)
    if not radar_rows:
        raise SystemExit("No radar rows found.")
    if not vision_rows:
        raise SystemExit("No vision rows found.")

    radar_root = radar_jsonl.parent
    radar_timestamps = [float(row["timestamp_ms"]) for row in radar_rows]
    aligned_rows: list[dict] = []
    discarded_count = 0

    state_counts = {
        "agree_positive": 0,
        "vision_only": 0,
        "radar_only": 0,
        "agree_negative": 0,
    }

    for vision_row in vision_rows:
        vision_timestamp = float(vision_row["timestamp_ms"])
        radar_row = nearest_radar_frame(radar_rows, radar_timestamps, vision_timestamp)
        if radar_row is None:
            discarded_count += 1
            continue

        time_delta_ms = abs(float(radar_row["timestamp_ms"]) - vision_timestamp)
        if time_delta_ms > args.max_time_delta_ms:
            discarded_count += 1
            continue

        detections = vision_row.get("detections", [])
        top_confidence = max((float(det.get("confidence", 0.0)) for det in detections), default=0.0)
        vision_positive = any(float(det.get("confidence", 0.0)) >= args.vision_conf_threshold for det in detections)
        radar_score = load_radar_score(radar_root / radar_row["img_path"])
        radar_positive = radar_score >= args.radar_score_threshold
        state = classify_state(vision_positive, radar_positive)
        state_counts[state] += 1

        aligned_rows.append(
            {
                "session_id": radar_row["session_id"],
                "vision_source_id": vision_row["source_id"],
                "vision_frame_id": int(vision_row["frame_id"]),
                "radar_frame_id": int(radar_row["frame_id"]),
                "vision_timestamp_ms": vision_timestamp,
                "radar_timestamp_ms": float(radar_row["timestamp_ms"]),
                "time_delta_ms": time_delta_ms,
                "vision_top_confidence": top_confidence,
                "radar_score": radar_score,
                "vision_positive": vision_positive,
                "radar_positive": radar_positive,
                "state": state,
                "radar_img_path": radar_row["img_path"],
            }
        )

    aligned_rows.sort(key=lambda row: row["vision_frame_id"])

    with (output_dir / "aligned_pairs.jsonl").open("w", encoding="utf-8") as handle:
        for row in aligned_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    with (output_dir / "fusion_review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "vision_frame_id",
                "radar_frame_id",
                "time_delta_ms",
                "vision_top_confidence",
                "radar_score",
                "state",
            ],
        )
        writer.writeheader()
        for row in aligned_rows:
            writer.writerow(
                {
                    "vision_frame_id": row["vision_frame_id"],
                    "radar_frame_id": row["radar_frame_id"],
                    "time_delta_ms": f"{row['time_delta_ms']:.3f}",
                    "vision_top_confidence": f"{row['vision_top_confidence']:.6f}",
                    "radar_score": f"{row['radar_score']:.6f}",
                    "state": row["state"],
                }
            )

    summary = {
        "session_id": radar_rows[0]["session_id"],
        "vision_source_id": vision_rows[0]["source_id"],
        "max_time_delta_ms": args.max_time_delta_ms,
        "vision_conf_threshold": args.vision_conf_threshold,
        "radar_score_threshold": args.radar_score_threshold,
        "aligned_pair_count": len(aligned_rows),
        "discarded_pair_count": discarded_count,
        **state_counts,
        "note": "该结果仅用于离线接口验证与决策级融合演示，不代表真实雷达-视觉配对性能。",
    }
    (output_dir / "fusion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    render_demo_video(
        aligned_rows=aligned_rows,
        overlay_path=overlay_path,
        radar_root=radar_root,
        output_path=output_dir / "fusion_demo.mp4",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
