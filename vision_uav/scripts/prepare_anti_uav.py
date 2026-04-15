#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
from tqdm import tqdm

from common import dump_yaml, ensure_dir, load_yaml, resolve_workspace_path


VALID_VIDEO_SUFFIXES = (".mp4", ".avi", ".mpg", ".mpeg")


@dataclass(frozen=True)
class SequenceSpec:
    name: str
    directory: Path
    video_path: Path
    label_path: Path
    split: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Anti-UAV RGB sequences to YOLO detect format.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/anti_uav_prepare.yaml",
        help="Path to the preparation YAML config.",
    )
    return parser.parse_args()


def discover_sequences(
    source_root: Path,
    rgb_video_name: str,
    rgb_label_name: str,
    include_prefixes: list[str],
    exclude_prefixes: list[str],
    use_existing_splits: bool,
    max_sequences: int | None,
    max_sequences_per_split: dict[str, int] | None,
) -> list[SequenceSpec]:
    sequences: list[SequenceSpec] = []
    if use_existing_splits:
        per_split_counts: dict[str, int] = defaultdict(int)
        for split_dir in sorted(source_root.iterdir()):
            if not split_dir.is_dir() or split_dir.name not in {"train", "val", "test"}:
                continue
            split = split_dir.name
            for child in sorted(split_dir.iterdir()):
                if not child.is_dir():
                    continue
                if include_prefixes and not any(child.name.startswith(prefix) for prefix in include_prefixes):
                    continue
                if exclude_prefixes and any(child.name.startswith(prefix) for prefix in exclude_prefixes):
                    continue
                if max_sequences_per_split and split in max_sequences_per_split:
                    if per_split_counts[split] >= int(max_sequences_per_split[split]):
                        continue
                video_path = child / rgb_video_name
                label_path = child / rgb_label_name
                if not video_path.exists() or not label_path.exists():
                    continue
                sequences.append(SequenceSpec(child.name, child, video_path, label_path, split=split))
                per_split_counts[split] += 1
    else:
        for child in sorted(source_root.iterdir()):
            if not child.is_dir():
                continue
            if include_prefixes and not any(child.name.startswith(prefix) for prefix in include_prefixes):
                continue
            if exclude_prefixes and any(child.name.startswith(prefix) for prefix in exclude_prefixes):
                continue

            video_path = child / rgb_video_name
            if not video_path.exists():
                alternatives = sorted(
                    [
                        file
                        for file in child.iterdir()
                        if file.is_file() and file.suffix.lower() in VALID_VIDEO_SUFFIXES and file.stem.lower() == "rgb"
                    ]
                )
                if alternatives:
                    video_path = alternatives[0]

            label_path = child / rgb_label_name
            if not label_path.exists():
                alternatives = sorted(
                    [
                        file
                        for file in child.iterdir()
                        if file.is_file() and file.name.lower() == rgb_label_name.lower()
                    ]
                )
                if alternatives:
                    label_path = alternatives[0]

            if not video_path.exists() or not label_path.exists():
                continue
            sequences.append(SequenceSpec(child.name, child, video_path, label_path))
    if max_sequences is not None and max_sequences > 0:
        return sequences[:max_sequences]
    return sequences


def allocate_splits(sequence_names: list[str], ratios: dict[str, float], seed: int) -> dict[str, str]:
    ordered = list(sorted(sequence_names))
    random.Random(seed).shuffle(ordered)
    total = len(ordered)
    if total == 0:
        raise ValueError("No Anti-UAV RGB sequences were found under the configured source_root.")

    train_count = max(1, round(total * float(ratios.get("train", 0.8))))
    val_count = round(total * float(ratios.get("val", 0.1)))
    test_count = total - train_count - val_count
    if total >= 3:
        if val_count == 0:
            val_count = 1
        if test_count == 0:
            test_count = 1
        train_count = max(1, total - val_count - test_count)

    while train_count + val_count + test_count > total:
        if train_count >= val_count and train_count >= test_count and train_count > 1:
            train_count -= 1
        elif val_count > 0:
            val_count -= 1
        else:
            test_count -= 1
    while train_count + val_count + test_count < total:
        train_count += 1

    mapping: dict[str, str] = {}
    for index, name in enumerate(ordered):
        if index < train_count:
            split = "train"
        elif index < train_count + val_count:
            split = "val"
        else:
            split = "test"
        mapping[name] = split
    return mapping


def load_annotations(label_path: Path) -> list[list[float]]:
    with label_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "gt_rect" not in payload or not isinstance(payload["gt_rect"], list):
        raise ValueError(f"{label_path} does not contain a valid gt_rect list.")
    return payload["gt_rect"]


def normalize_bbox(raw_bbox: list[float], width: int, height: int) -> str | None:
    if len(raw_bbox) != 4:
        return None
    x, y, w, h = [float(value) for value in raw_bbox]
    if w <= 0 or h <= 0:
        return None
    x = max(0.0, min(x, width - 1.0))
    y = max(0.0, min(y, height - 1.0))
    w = max(0.0, min(w, width - x))
    h = max(0.0, min(h, height - y))
    if w <= 1e-6 or h <= 1e-6:
        return None
    cx = (x + w / 2.0) / width
    cy = (y + h / 2.0) / height
    nw = w / width
    nh = h / height
    return f"0 {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n"


def write_image_unicode_safe(image_path: Path, frame) -> None:
    suffix = image_path.suffix.lower()
    extension = ".jpg" if suffix not in {".jpg", ".jpeg", ".png", ".bmp"} else suffix
    success, encoded = cv2.imencode(extension, frame)
    if not success:
        raise RuntimeError(f"Failed to encode frame for output: {image_path}")
    encoded.tofile(str(image_path))


def convert_sequences(
    sequences: list[SequenceSpec],
    split_map: dict[str, str],
    output_root: Path,
    dataset_path_alias: str | None,
    dataset_yaml_name: str,
    frame_stride: dict[str, int],
    class_name: str,
) -> dict[str, Any]:
    images_root = output_root / "images"
    labels_root = output_root / "labels"
    meta_root = ensure_dir(output_root / "meta")
    stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    manifest: list[dict[str, Any]] = []

    for split in ("train", "val", "test"):
        ensure_dir(images_root / split)
        ensure_dir(labels_root / split)

    for sequence in tqdm(sequences, desc="Converting Anti-UAV RGB sequences"):
        split = sequence.split or split_map[sequence.name]
        stride = max(1, int(frame_stride.get(split, 1)))
        annotations = load_annotations(sequence.label_path)

        capture = cv2.VideoCapture(str(sequence.video_path))
        if not capture.isOpened():
            raise RuntimeError(f"Failed to open video: {sequence.video_path}")

        frame_index = 0
        exported_frames = 0
        kept_positive_frames = 0

        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_index >= len(annotations):
                break
            if frame_index % stride != 0:
                frame_index += 1
                continue

            height, width = frame.shape[:2]
            stem = f"{sequence.name}_RGB_{frame_index:06d}"
            image_path = images_root / split / f"{stem}.jpg"
            label_path = labels_root / split / f"{stem}.txt"

            write_image_unicode_safe(image_path, frame)
            label_text = normalize_bbox(annotations[frame_index], width, height)
            with label_path.open("w", encoding="utf-8", newline="\n") as handle:
                if label_text is not None:
                    handle.write(label_text)
                    kept_positive_frames += 1

            manifest.append(
                {
                    "split": split,
                    "sequence": sequence.name,
                    "frame_index": frame_index,
                    "image": str(image_path.relative_to(output_root)).replace("\\", "/"),
                    "label": str(label_path.relative_to(output_root)).replace("\\", "/"),
                    "has_target": label_text is not None,
                }
            )
            exported_frames += 1
            frame_index += 1

        capture.release()
        stats[split]["sequences"] += 1
        stats[split]["frames"] += exported_frames
        stats[split]["positive_frames"] += kept_positive_frames
        stats[split]["empty_frames"] += exported_frames - kept_positive_frames

    with (meta_root / "sequence_splits.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(split_map, handle, indent=2, ensure_ascii=False)
    with (meta_root / "manifest.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in manifest:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (meta_root / "stats.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(stats, handle, indent=2, ensure_ascii=False)

    dataset_yaml = {
        "path": dataset_path_alias or str(output_root),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: class_name},
    }
    dump_yaml(output_root / dataset_yaml_name, dataset_yaml)
    return {"stats": stats, "dataset_yaml": output_root / dataset_yaml_name}


def main() -> int:
    args = parse_args()
    config_path = resolve_workspace_path(args.config)
    config = load_yaml(config_path)

    source_root = resolve_workspace_path(str(config["source_root"]))
    output_root = resolve_workspace_path(str(config["output_root"]))
    ensure_dir(output_root)

    filters = config.get("sequence_filters", {})
    paths = config.get("paths", {})
    use_existing_splits = bool(config.get("use_existing_splits", False))
    max_sequences_per_split = config.get("max_sequences_per_split")
    sequences = discover_sequences(
        source_root=source_root,
        rgb_video_name=str(paths.get("rgb_video_name", "RGB.mp4")),
        rgb_label_name=str(paths.get("rgb_label_name", "RGB_label.json")),
        include_prefixes=list(filters.get("include_prefixes", [])),
        exclude_prefixes=list(filters.get("exclude_prefixes", [])),
        use_existing_splits=use_existing_splits,
        max_sequences=int(config["max_sequences"]) if config.get("max_sequences") is not None else None,
        max_sequences_per_split=dict(max_sequences_per_split) if max_sequences_per_split is not None else None,
    )
    if use_existing_splits:
        split_map = {sequence.name: sequence.split or "train" for sequence in sequences}
    else:
        split_map = allocate_splits(
            [sequence.name for sequence in sequences],
            ratios=dict(config.get("split_ratios", {})),
            seed=int(config.get("seed", 20260415)),
        )
    result = convert_sequences(
        sequences=sequences,
        split_map=split_map,
        output_root=output_root,
        dataset_path_alias=str(config["dataset_path_alias"]) if config.get("dataset_path_alias") else None,
        dataset_yaml_name=str(config.get("dataset_yaml_name", "anti_uav_rgb_detect.yaml")),
        frame_stride=dict(config.get("frame_stride", {})),
        class_name=str(config.get("class_name", "uav")),
    )

    print(f"source_root={source_root}")
    print(f"output_root={output_root}")
    print(f"dataset_yaml={result['dataset_yaml']}")
    for split in ("train", "val", "test"):
        split_stats = result["stats"].get(split, {})
        print(
            f"{split}: "
            f"sequences={split_stats.get('sequences', 0)} "
            f"frames={split_stats.get('frames', 0)} "
            f"positive_frames={split_stats.get('positive_frames', 0)} "
            f"empty_frames={split_stats.get('empty_frames', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
