#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import cv2
import numpy as np

from common import ensure_dir, load_yaml, resolve_workspace_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split Anti-UAV empty-label frames into pure-sky and clutter background pools."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/scene_hard_negative_pools.yaml",
        help="Path to the scene hard-negative YAML config.",
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


def compute_sky_ratio_and_edge_density(
    image_path: Path,
    canny_low_threshold: int,
    canny_high_threshold: int,
    gaussian_blur_kernel: int,
    edge_dilate_kernel: int,
) -> tuple[float, float]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise RuntimeError(f"Failed to read image: {image_path}")
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower = np.array([90, 10, 40], dtype=np.uint8)
    upper = np.array([140, 180, 255], dtype=np.uint8)
    sky_mask = cv2.inRange(hsv, lower, upper)
    sky_ratio = float(np.count_nonzero(sky_mask)) / float(sky_mask.size)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (gaussian_blur_kernel, gaussian_blur_kernel), 0)
    edges = cv2.Canny(gray, canny_low_threshold, canny_high_threshold)
    edges = cv2.dilate(
        edges,
        np.ones((edge_dilate_kernel, edge_dilate_kernel), dtype=np.uint8),
        iterations=1,
    )
    edge_density = float(np.count_nonzero(edges)) / float(edges.size)
    return sky_ratio, edge_density


def copy_with_meta(source_path: Path, destination_dir: Path, split: str, base_name: str) -> str:
    ensure_dir(destination_dir)
    destination_name = f"{split}_{base_name}{source_path.suffix.lower()}"
    destination_path = destination_dir / destination_name
    if not destination_path.exists():
        shutil.copy2(source_path, destination_path)
    return destination_name


def sample_records(records: list[dict], target: int) -> list[dict]:
    records = sorted(records, key=lambda row: row["file_name"])
    return records[:target]


def write_suite(output_dir: Path, records: list[dict], suite_name: str) -> dict:
    images_dir = ensure_dir(output_dir / "images")
    manifest_records: list[dict] = []
    for record in records:
        source_path = Path(record["source_path"])
        destination_name = copy_with_meta(source_path, images_dir, record["split"], source_path.stem)
        manifest_records.append(
            {
                "source_path": record["source_path"],
                "file_name": destination_name,
                "split": record["split"],
                "sky_ratio": record["sky_ratio"],
                "edge_density": record["edge_density"],
            }
        )
    summary = {
        "suite_name": suite_name,
        "image_count": len(manifest_records),
        "images_dir": str(images_dir),
        "records": manifest_records,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    source_root = resolve_workspace_path(config["source_root"])
    raw_output_root = ensure_dir(resolve_workspace_path(config["raw_output_root"]))
    processed_output_root = ensure_dir(resolve_workspace_path(config["processed_output_root"]))

    pure_sky_pool_name = str(config["pure_sky_pool_name"])
    clutter_pool_name = str(config["clutter_pool_name"])
    sky_eval_suite_name = str(config["sky_eval_suite_name"])
    clutter_eval_suite_name = str(config["clutter_eval_suite_name"])
    canny_low_threshold = int(config["canny_low_threshold"])
    canny_high_threshold = int(config["canny_high_threshold"])
    gaussian_blur_kernel = int(config["gaussian_blur_kernel"])
    edge_dilate_kernel = int(config["edge_dilate_kernel"])

    pure_sky_records: list[dict] = []
    clutter_records: list[dict] = []

    for split in config["pool_splits"]:
        label_dir = source_root / "labels" / str(split)
        for label_path in sorted(label_dir.glob("*.txt")):
            if label_path.stat().st_size != 0:
                continue
            image_path = image_for_label(source_root, str(split), label_path)
            if image_path is None:
                continue
            sky_ratio, edge_density = compute_sky_ratio_and_edge_density(
                image_path,
                canny_low_threshold,
                canny_high_threshold,
                gaussian_blur_kernel,
                edge_dilate_kernel,
            )
            record = {
                "source_path": str(image_path),
                "file_name": image_path.name,
                "split": str(split),
                "sky_ratio": round(sky_ratio, 6),
                "edge_density": round(edge_density, 6),
            }
            if (
                sky_ratio >= float(config["pure_sky_ratio_min"])
                and edge_density <= float(config["pure_sky_edge_density_max"])
            ):
                pure_sky_records.append(record)
            elif (
                sky_ratio < float(config["clutter_sky_ratio_max"])
                and edge_density >= float(config["clutter_edge_density_min"])
            ):
                clutter_records.append(record)

    pure_sky_pool_dir = ensure_dir(raw_output_root / pure_sky_pool_name)
    clutter_pool_dir = ensure_dir(raw_output_root / clutter_pool_name)

    for record in pure_sky_records:
        source_path = Path(record["source_path"])
        copy_with_meta(source_path, ensure_dir(pure_sky_pool_dir / "images"), record["split"], source_path.stem)
    for record in clutter_records:
        source_path = Path(record["source_path"])
        copy_with_meta(source_path, ensure_dir(clutter_pool_dir / "images"), record["split"], source_path.stem)

    eval_splits = {str(value) for value in config["eval_splits"]}
    sky_eval_records = [record for record in pure_sky_records if record["split"] in eval_splits]
    clutter_eval_records = [record for record in clutter_records if record["split"] in eval_splits]

    sky_summary = write_suite(
        processed_output_root / sky_eval_suite_name,
        sample_records(sky_eval_records, int(config["sky_eval_target_images"])),
        sky_eval_suite_name,
    )
    clutter_summary = write_suite(
        processed_output_root / clutter_eval_suite_name,
        sample_records(clutter_eval_records, int(config["clutter_eval_target_images"])),
        clutter_eval_suite_name,
    )

    summary = {
        "pure_sky_pool": {
            "output_dir": str(pure_sky_pool_dir),
            "candidate_count": len(pure_sky_records),
        },
        "clutter_background_pool": {
            "output_dir": str(clutter_pool_dir),
            "candidate_count": len(clutter_records),
        },
        "sky_eval": sky_summary,
        "clutter_eval": clutter_summary,
        "metric_config": {
            "canny_low_threshold": canny_low_threshold,
            "canny_high_threshold": canny_high_threshold,
            "gaussian_blur_kernel": gaussian_blur_kernel,
            "edge_dilate_kernel": edge_dilate_kernel,
        },
    }
    summary_path = raw_output_root / "scene_pool_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"summary_json={summary_path}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
