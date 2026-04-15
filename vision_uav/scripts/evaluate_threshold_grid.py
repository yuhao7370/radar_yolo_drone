#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from common import extract_detection_metrics, load_yaml, load_yolo_model, resolve_workspace_path
from evaluate import resolve_eval_args


RESERVED_KEYS = {"weights", "fallback_model", "thresholds", "splits", "baseline_metrics", "acceptance", "project", "name"}


def resolve_threshold_eval_args(config: dict) -> dict:
    eval_config = {key: value for key, value in config.items() if key not in RESERVED_KEYS}
    return resolve_eval_args(eval_config)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a model on val/test across a threshold grid."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/eval_threshold_grid_hn_v2.yaml",
        help="Path to the threshold-grid evaluation YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    weights = args.weights or str(config["weights"])
    fallback_model = config.get("fallback_model")
    model = load_yolo_model(weights, str(fallback_model) if fallback_model else None)

    output_root = Path(resolve_workspace_path(config["project"])) / str(config["name"])
    output_root.mkdir(parents=True, exist_ok=True)
    thresholds = [float(value) for value in config["thresholds"]]

    rows: list[dict] = []
    for split in config["splits"]:
        eval_args = resolve_threshold_eval_args(config)
        eval_args["split"] = str(split)
        for threshold in thresholds:
            eval_args["conf"] = threshold
            metrics = model.val(**eval_args)
            summary = extract_detection_metrics(metrics)
            rows.append(
                {
                    "split": str(split),
                    "threshold": threshold,
                    "precision": summary["precision"],
                    "recall": summary["recall"],
                    "mAP50": summary["mAP50"],
                    "mAP50-95": summary["mAP50-95"],
                }
            )

    csv_path = output_root / "threshold_grid.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["split", "threshold", "precision", "recall", "mAP50", "mAP50-95"],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = {"weights": str(resolve_workspace_path(weights)), "rows": rows}
    (output_root / "threshold_grid_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_root={output_root}")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
