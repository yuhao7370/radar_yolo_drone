#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from common import ensure_dir, load_yaml, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a combined bird_eval_public suite from Distant Bird images and FBD-SV val videos."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/bird_eval_public_suite.yaml",
        help="Path to the bird_eval_public suite YAML config.",
    )
    return parser.parse_args()


def load_existing_records(manifest_path: Path) -> list[dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = []
    for item in manifest.get("images", []):
        records.append(
            {
                "source": "distant_bird_detection",
                "source_path": item["source_path"],
                "file_name": item["local_name"],
                "object_count": item.get("object_count", 0),
                "labels": item.get("labels", []),
            }
        )
    return records


def sample_fbd_sv_frames(
    video_dir: Path,
    images_dir: Path,
    frame_stride: int,
    max_frames_per_video: int,
    target_images: int,
) -> list[dict]:
    records: list[dict] = []
    for video_path in sorted(video_dir.glob("*.mp4")):
        if len(records) >= target_images:
            break
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        saved = 0
        frame_idx = 0
        try:
            while saved < max_frames_per_video and len(records) < target_images:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_idx % frame_stride == 0:
                    file_name = f"fbdsv_{video_path.stem}_{frame_idx:06d}.jpg"
                    destination = images_dir / file_name
                    if not destination.exists():
                        if not cv2.imwrite(str(destination), frame):
                            raise RuntimeError(f"Failed to write sampled frame: {destination}")
                    records.append(
                        {
                            "source": "fbd_sv_2024",
                            "source_path": str(video_path),
                            "file_name": file_name,
                            "object_count": 0,
                            "labels": [],
                        }
                    )
                    saved += 1
                frame_idx += 1
        finally:
            capture.release()
    return records


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    manifest_path = resolve_workspace_path(config["distant_bird_manifest"])
    fbd_sv_val_dir = resolve_workspace_path(config["fbd_sv_val_dir"])
    output_root = ensure_dir(resolve_workspace_path(config["output_root"]))
    images_dir = ensure_dir(output_root / "images")

    existing_records = load_existing_records(manifest_path)
    fbd_sv_records = sample_fbd_sv_frames(
        fbd_sv_val_dir,
        images_dir,
        frame_stride=int(config["frame_stride"]),
        max_frames_per_video=int(config["max_frames_per_video"]),
        target_images=int(config["fbd_sv_target_images"]),
    )

    combined_records = existing_records + fbd_sv_records
    manifest = {
        "suite_name": "bird_eval_public",
        "image_count": len(combined_records),
        "images_dir": str(images_dir),
        "records": combined_records,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_root={output_root}")
    print(json.dumps({"image_count": len(combined_records), "fbd_sv_added": len(fbd_sv_records)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
