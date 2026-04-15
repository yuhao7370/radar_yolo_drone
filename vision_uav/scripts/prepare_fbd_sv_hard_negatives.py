#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import cv2
import yaml

from common import ensure_dir, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare bird hard-negative samples from the FBD-SV-2024 zip archive."
    )
    parser.add_argument(
        "--zip-path",
        default="vision_uav/data/raw/hard_negatives/fbd_sv_2024/FBD-SV-2024.zip",
        help="Path to the downloaded FBD-SV-2024 zip archive.",
    )
    parser.add_argument(
        "--raw-output-root",
        default="vision_uav/data/raw/hard_negatives/fbd_sv_2024",
        help="Directory used to store selected raw bird videos.",
    )
    parser.add_argument(
        "--processed-output-root",
        default="vision_uav/data/processed/anti_uav_rgb_detect_hn",
        help="Directory used to store bird hard-negative training images and dataset yaml.",
    )
    parser.add_argument("--train-video-count", type=int, default=12, help="Number of training videos to extract.")
    parser.add_argument("--val-video-count", type=int, default=4, help="Number of validation videos to extract.")
    parser.add_argument("--train-frame-stride", type=int, default=10, help="Frame stride for bird train-image extraction.")
    parser.add_argument(
        "--max-frames-per-train-video",
        type=int,
        default=80,
        help="Maximum number of sampled frames per extracted train video.",
    )
    return parser.parse_args()


def extract_selected(zip_path: Path, members: list[str], destination_root: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in members:
            relative = Path(member).relative_to("FBD-SV-2024")
            destination = destination_root / relative
            if not destination.exists():
                ensure_dir(destination.parent)
                with zf.open(member) as src, destination.open("wb") as dst:
                    dst.write(src.read())
            extracted.append(destination)
    return extracted


def sample_train_frames(
    video_paths: list[Path],
    images_dir: Path,
    labels_dir: Path,
    frame_stride: int,
    max_frames_per_video: int,
) -> dict[str, int]:
    summary: dict[str, int] = {}
    ensure_dir(images_dir)
    ensure_dir(labels_dir)

    for video_path in video_paths:
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open video: {video_path}")
        saved = 0
        frame_idx = 0
        stem = video_path.stem
        try:
            while saved < max_frames_per_video:
                ok, frame = capture.read()
                if not ok:
                    break
                if frame_idx % frame_stride == 0:
                    image_name = f"{stem}_{frame_idx:06d}.jpg"
                    image_path = images_dir / image_name
                    if not cv2.imwrite(str(image_path), frame):
                        raise RuntimeError(f"Failed to write sampled frame: {image_path}")
                    (labels_dir / f"{stem}_{frame_idx:06d}.txt").write_text("", encoding="utf-8")
                    saved += 1
                frame_idx += 1
        finally:
            capture.release()
        summary[video_path.name] = saved
    return summary


def build_train_list(base_dataset_root: Path, processed_output_root: Path) -> Path:
    train_images = sorted((base_dataset_root / "images" / "train").glob("*"))
    bird_images = sorted((processed_output_root / "images" / "train_birds").glob("*.jpg"))
    train_list_path = processed_output_root / "train_hn.txt"
    lines = [f"../anti_uav_rgb_detect/images/train/{path.name}" for path in train_images if path.is_file()]
    lines.extend([f"images/train_birds/{path.name}" for path in bird_images])
    train_list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return train_list_path


def write_dataset_yaml(processed_output_root: Path) -> Path:
    yaml_path = processed_output_root / "anti_uav_rgb_detect_hn.yaml"
    data = {
        "path": ".",
        "train": "train_hn.txt",
        "val": "../anti_uav_rgb_detect/images/val",
        "test": "../anti_uav_rgb_detect/images/test",
        "names": {0: "uav"},
    }
    yaml_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return yaml_path


def main() -> int:
    args = parse_args()
    zip_path = resolve_workspace_path(args.zip_path)
    raw_output_root = ensure_dir(resolve_workspace_path(args.raw_output_root))
    processed_output_root = ensure_dir(resolve_workspace_path(args.processed_output_root))
    base_dataset_root = resolve_workspace_path("vision_uav/data/processed/anti_uav_rgb_detect")

    with zipfile.ZipFile(zip_path, "r") as zf:
        train_members = sorted(
            name for name in zf.namelist()
            if name.startswith("FBD-SV-2024/videos/train/") and name.lower().endswith(".mp4")
        )[: args.train_video_count]
        val_members = sorted(
            name for name in zf.namelist()
            if name.startswith("FBD-SV-2024/videos/val/") and name.lower().endswith(".mp4")
        )[: args.val_video_count]

    train_videos = extract_selected(zip_path, train_members, raw_output_root)
    val_videos = extract_selected(zip_path, val_members, raw_output_root)

    sampled = sample_train_frames(
        train_videos,
        processed_output_root / "images" / "train_birds",
        processed_output_root / "labels" / "train_birds",
        args.train_frame_stride,
        args.max_frames_per_train_video,
    )
    train_list_path = build_train_list(base_dataset_root, processed_output_root)
    yaml_path = write_dataset_yaml(processed_output_root)

    summary = {
        "train_videos": [str(path) for path in train_videos],
        "val_videos": [str(path) for path in val_videos],
        "sampled_train_frames": sampled,
        "train_list": str(train_list_path),
        "dataset_yaml": str(yaml_path),
    }
    summary_path = processed_output_root / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"raw_output_root={raw_output_root}")
    print(f"processed_output_root={processed_output_root}")
    print(f"summary_json={summary_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
