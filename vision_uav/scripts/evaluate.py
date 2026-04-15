#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from common import load_yaml, resolve_workspace_path


PATH_KEYS = {"weights", "data", "project"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate a trained YOLO model for vision_uav.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/eval_baseline.yaml",
        help="Path to the evaluation YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def resolve_eval_args(config: dict[str, Any]) -> dict[str, Any]:
    eval_args: dict[str, Any] = {}
    for key, value in config.items():
        if key == "weights":
            continue
        if key in PATH_KEYS:
            eval_args[key] = str(resolve_workspace_path(Path(str(value))))
        else:
            eval_args[key] = value
    return eval_args


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    weights = args.weights or str(config["weights"])

    model = YOLO(str(resolve_workspace_path(weights)))
    eval_args = resolve_eval_args(config)
    metrics = model.val(**eval_args)

    save_dir = getattr(metrics, "save_dir", None)
    if save_dir is not None:
        print(f"save_dir={save_dir}")
    print("evaluation=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
