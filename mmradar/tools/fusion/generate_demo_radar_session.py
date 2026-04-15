#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a demo radar export session aligned to vision predictions."
    )
    parser.add_argument("--vision-predictions", required=True, help="Path to predictions.jsonl")
    parser.add_argument("--output-dir", required=True, help="Radar session output directory")
    parser.add_argument("--session-id", default="demo_session", help="Fusion session id")
    parser.add_argument("--time-offset-ms", type=float, default=30.0, help="Radar timestamp offset")
    parser.add_argument("--img-x", type=float, default=-2.0)
    parser.add_argument("--img-y", type=float, default=2.5)
    parser.add_argument("--img-w", type=float, default=5.0)
    parser.add_argument("--img-h", type=float, default=8.0)
    parser.add_argument("--grid-x", type=int, default=500)
    parser.add_argument("--grid-y", type=int, default=800)
    parser.add_argument("--sar-height", type=float, default=0.872)
    parser.add_argument("--speed", type=float, default=0.12)
    parser.add_argument(
        "--snapshot-stride-trip",
        type=int,
        default=1,
        help="Only for metadata. The demo export writes one frame per vision frame.",
    )
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


def radar_positive_for_frame(frame_id: int) -> bool:
    cycle = frame_id % 8
    return cycle in (0, 1, 4, 5)


def render_radar_frame(width: int, height: int, frame_id: int, positive: bool) -> np.ndarray:
    image = np.full((height, width), 18, dtype=np.uint8)
    image += np.linspace(0, 22, width, dtype=np.uint8)[None, :]
    center_x = int(width * (0.15 + 0.7 * ((frame_id % 37) / 36.0)))
    center_y = int(height * (0.2 + 0.6 * (((frame_id * 3) % 41) / 40.0)))
    radius = 18 + (frame_id % 9)
    peak = 220 if positive else 110
    cv2.circle(image, (center_x, center_y), radius, int(peak), -1)
    cv2.circle(image, (center_x, center_y), max(6, radius // 3), 255 if positive else 145, -1)
    return image


def main() -> None:
    args = parse_args()
    predictions_path = Path(args.vision_predictions)
    output_dir = Path(args.output_dir)
    frames_dir = output_dir / "frames"
    output_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    vision_rows = read_jsonl(predictions_path)
    if not vision_rows:
        raise SystemExit("No frames found in predictions.jsonl")

    final_res = np.zeros((args.grid_y, args.grid_x), dtype=np.uint8)
    radar_rows: list[dict] = []

    for row in vision_rows:
        frame_id = int(row["frame_id"])
        timestamp_ms = float(row["timestamp_ms"]) + args.time_offset_ms
        now_pt = int(round(timestamp_ms * 1000.0))
        positive = radar_positive_for_frame(frame_id)
        frame_img = render_radar_frame(args.grid_x, args.grid_y, frame_id, positive)
        final_res = np.maximum(final_res, frame_img)

        rel_path = f"frames/frame_{frame_id:06d}.jpg"
        full_path = output_dir / rel_path
        cv2.imwrite(str(full_path), frame_img, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

        radar_rows.append(
            {
                "session_id": args.session_id,
                "frame_id": frame_id,
                "trip_idx": frame_id,
                "now_pt": now_pt,
                "timestamp_ms": timestamp_ms,
                "sar_pos_x_m": args.speed * now_pt / 1_000_000.0,
                "img_path": rel_path.replace("\\", "/"),
                "img_x": args.img_x,
                "img_y": args.img_y,
                "img_w": args.img_w,
                "img_h": args.img_h,
                "grid_x": args.grid_x,
                "grid_y": args.grid_y,
                "sar_height": args.sar_height,
                "speed": args.speed,
            }
        )

    with (output_dir / "radar_frames.jsonl").open("w", encoding="utf-8") as handle:
        for row in radar_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    session_meta = {
        "session_id": args.session_id,
        "source_file": str(predictions_path),
        "trip_len": 0,
        "trip_num": len(radar_rows),
        "snapshot_stride_trip": max(1, args.snapshot_stride_trip),
        "img_x": args.img_x,
        "img_y": args.img_y,
        "img_w": args.img_w,
        "img_h": args.img_h,
        "grid_x": args.grid_x,
        "grid_y": args.grid_y,
        "sar_height": args.sar_height,
        "speed": args.speed,
        "export_mode": "demo_bp_snapshot_mvp",
        "note": "该会话由视觉预测结果派生生成，仅用于离线融合接口和可视化演示，不代表真实雷达同步采样。",
    }
    (output_dir / "session_meta.json").write_text(
        json.dumps(session_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    cv2.imwrite(
        str(output_dir / "final_res.jpg"),
        final_res,
        [int(cv2.IMWRITE_JPEG_QUALITY), 100],
    )

    demo_summary = {
        "session_id": args.session_id,
        "frame_count": len(radar_rows),
        "time_offset_ms": args.time_offset_ms,
        "positive_frame_count": sum(1 for row in radar_rows if radar_positive_for_frame(int(row["frame_id"]))),
        "negative_frame_count": sum(1 for row in radar_rows if not radar_positive_for_frame(int(row["frame_id"]))),
    }
    (output_dir / "demo_summary.json").write_text(
        json.dumps(demo_summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(demo_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
