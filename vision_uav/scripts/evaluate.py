#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import extract_detection_metrics, load_yaml, load_yolo_model, resolve_workspace_path


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


def run_evaluation(config_path: str | Path, weights_override: str | None = None) -> dict[str, Any]:
    config = load_yaml(resolve_workspace_path(config_path))
    weights = weights_override or str(config["weights"])
    model = load_yolo_model(weights)
    eval_args = resolve_eval_args(config)
    metrics = model.val(**eval_args)
    save_dir = getattr(metrics, "save_dir", None)
    return {
        "config": config,
        "metrics": metrics,
        "summary": extract_detection_metrics(metrics),
        "save_dir": Path(save_dir) if save_dir is not None else None,
    }


def main() -> int:
    args = parse_args()
    result = run_evaluation(args.config, args.weights)
    if result["save_dir"] is not None:
        print(f"save_dir={result['save_dir']}")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("evaluation=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
