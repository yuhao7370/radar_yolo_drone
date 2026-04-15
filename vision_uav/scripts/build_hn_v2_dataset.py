#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from common import ensure_dir, load_yaml, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build anti_uav_rgb_detect_hn_v2 from mined hard-negative selections."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/hard_negative_round2_mining.yaml",
        help="Path to the hard-negative mining YAML config.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    base_dataset_root = resolve_workspace_path(config["base_dataset_root"])
    mining_root = resolve_workspace_path(config["project"]) / str(config["name"])
    output_root = ensure_dir(resolve_workspace_path(config["hn_v2_output_root"]))
    processed_root = base_dataset_root.parent

    train_images = sorted((base_dataset_root / "images" / "train").glob("*"))
    train_lines = [str(path) for path in train_images if path.is_file()]

    selected_total = 0
    selected_by_category: dict[str, int] = {}
    for category in ["bird", "pure_sky", "clutter"]:
        selected_path = mining_root / f"{category}_selected.json"
        rows = json.loads(selected_path.read_text(encoding="utf-8")) if selected_path.exists() else []
        category_dir = ensure_dir(output_root / "images" / category)
        label_dir = ensure_dir(output_root / "labels" / category)
        selected_by_category[category] = len(rows)
        for row in rows:
            saved_path_str = str(row["saved_path"])
            source_path = Path(saved_path_str)
            if not source_path.exists():
                source_name = saved_path_str.replace("\\", "/").split("/")[-1]
                source_path = mining_root / category / source_name
            destination = category_dir / source_path.name
            if not destination.exists():
                destination.write_bytes(source_path.read_bytes())
            (label_dir / f"{destination.stem}.txt").write_text("", encoding="utf-8")
            train_lines.append(str(destination))
        selected_total += len(rows)

    train_list_path = output_root / "train_hn_v2.txt"
    train_list_path.write_text("\n".join(train_lines) + "\n", encoding="utf-8")

    dataset_yaml = {
        "path": str(processed_root),
        "train": "anti_uav_rgb_detect_hn_v2/train_hn_v2.txt",
        "val": "anti_uav_rgb_detect/images/val",
        "test": "anti_uav_rgb_detect/images/test",
        "names": {0: "uav"},
    }
    yaml_path = output_root / "anti_uav_rgb_detect_hn_v2.yaml"
    yaml_path.write_text(yaml.safe_dump(dataset_yaml, sort_keys=False, allow_unicode=True), encoding="utf-8")

    summary = {
        "base_train_images": len(train_images),
        "selected_total_hard_negatives": selected_total,
        "selected_by_category": selected_by_category,
        "train_list": str(train_list_path),
        "dataset_yaml": str(yaml_path),
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_root={output_root}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
