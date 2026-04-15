#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from common import ensure_dir, resolve_workspace_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract empty-label Anti-UAV frames as reproducible hard-negative image directories."
    )
    parser.add_argument(
        "--source-root",
        default="vision_uav/data/processed/anti_uav_rgb_detect",
        help="YOLO detect dataset root that contains images/ and labels/.",
    )
    parser.add_argument(
        "--output-root",
        default="vision_uav/data/raw/hard_negatives/anti_uav_background_only",
        help="Output directory for extracted hard-negative images.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["val", "test"],
        help="Dataset splits to scan for empty-label frames.",
    )
    return parser.parse_args()


def image_for_label(source_root: Path, split: str, label_path: Path) -> Path | None:
    base = label_path.stem
    image_dir = source_root / "images" / split
    for suffix in IMAGE_SUFFIXES:
        candidate = image_dir / f"{base}{suffix}"
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    args = parse_args()
    source_root = resolve_workspace_path(args.source_root)
    output_root = ensure_dir(resolve_workspace_path(args.output_root))

    summary: dict[str, dict[str, int]] = {}

    for split in args.splits:
        label_dir = source_root / "labels" / split
        out_dir = ensure_dir(output_root / split)
        copied = 0
        missing_images = 0

        if not label_dir.exists():
            raise FileNotFoundError(f"Split label directory not found: {label_dir}")

        for label_path in sorted(label_dir.glob("*.txt")):
            if label_path.stat().st_size != 0:
                continue
            image_path = image_for_label(source_root, split, label_path)
            if image_path is None:
                missing_images += 1
                continue
            shutil.copy2(image_path, out_dir / image_path.name)
            copied += 1

        summary[split] = {
            "copied_images": copied,
            "missing_images": missing_images,
        }

    summary_path = output_root / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output_root={output_root}")
    print(f"summary_json={summary_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
