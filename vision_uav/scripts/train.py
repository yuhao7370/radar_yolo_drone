#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from ultralytics import YOLO

from common import load_yaml, resolve_workspace_path


RESERVED_KEYS = {"model", "fallback_model", "task"}
PATH_KEYS = {"data", "project"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a YOLO model for vision_uav.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/train_smoke.yaml",
        help="Path to the training YAML config.",
    )
    parser.add_argument("--model", help="Optional explicit model override.", default=None)
    return parser.parse_args()


def resolve_train_args(config: dict[str, Any]) -> dict[str, Any]:
    train_args: dict[str, Any] = {}
    for key, value in config.items():
        if key in RESERVED_KEYS:
            continue
        if key in PATH_KEYS:
            train_args[key] = str(resolve_workspace_path(Path(str(value))))
        else:
            train_args[key] = value
    return train_args


def load_model(model_name: str, fallback_model: str | None) -> YOLO:
    try:
        return YOLO(model_name)
    except Exception:
        if fallback_model is None:
            raise
        print(f"primary_model_failed={model_name}")
        print(f"fallback_model={fallback_model}")
        return YOLO(fallback_model)


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    model_name = args.model or str(config["model"])
    fallback_model = config.get("fallback_model")

    model = load_model(model_name, str(fallback_model) if fallback_model else None)
    train_args = resolve_train_args(config)
    results = model.train(**train_args)

    save_dir = getattr(results, "save_dir", None)
    if save_dir is not None:
        print(f"save_dir={save_dir}")
    print(f"trained_model={model.model_name if hasattr(model, 'model_name') else model_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
