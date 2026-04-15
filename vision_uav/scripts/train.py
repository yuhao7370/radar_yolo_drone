#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import load_yaml, load_yolo_model, resolve_workspace_path


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


def run_train(config_path: str | Path, model_override: str | None = None) -> dict[str, Any]:
    config = load_yaml(resolve_workspace_path(config_path))
    model_name = model_override or str(config["model"])
    fallback_model = config.get("fallback_model")
    model = load_yolo_model(model_name, str(fallback_model) if fallback_model else None)
    train_args = resolve_train_args(config)
    results = model.train(**train_args)
    save_dir = getattr(results, "save_dir", None)
    return {
        "config": config,
        "train_args": train_args,
        "save_dir": Path(save_dir) if save_dir is not None else None,
        "trained_model": model_name,
    }


def main() -> int:
    args = parse_args()
    result = run_train(args.config, args.model)
    if result["save_dir"] is not None:
        print(f"save_dir={result['save_dir']}")
    print(f"trained_model={result['trained_model']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
