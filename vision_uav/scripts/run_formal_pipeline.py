#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from common import data_root_alias, ensure_dir, load_yaml, resolve_workspace_path, workspace_root_alias
from evaluate import run_evaluation
from export_onnx import run_export
from infer_video import run_inference
from train import run_train


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full formal YOLO26s training pipeline.")
    parser.add_argument(
        "--phase",
        choices=["probe", "full"],
        default="full",
        help="Run only the probe or the full formal pipeline.",
    )
    parser.add_argument(
        "--probe-config",
        default="vision_uav/configs/train_probe_full_yolo26s.yaml",
        help="Probe training config path.",
    )
    parser.add_argument(
        "--formal-config-b8",
        default="vision_uav/configs/train_full_yolo26s_nightly_b8.yaml",
        help="Primary nightly formal training config.",
    )
    parser.add_argument(
        "--formal-config-b4",
        default="vision_uav/configs/train_full_yolo26s_nightly_b4.yaml",
        help="Fallback nightly formal training config.",
    )
    parser.add_argument(
        "--eval-config",
        default="vision_uav/configs/eval_full_test_yolo26s.yaml",
        help="Formal test evaluation config path.",
    )
    parser.add_argument(
        "--infer-config",
        default="vision_uav/configs/infer_video.yaml",
        help="Inference config used as a base for real test videos.",
    )
    parser.add_argument(
        "--export-config",
        default="vision_uav/configs/export_onnx_formal.yaml",
        help="Formal ONNX export config path.",
    )
    parser.add_argument(
        "--test-root",
        default="vision_uav/data/raw/anti_uav/Anti-UAV300/test",
        help="Root folder containing the real Anti-UAV test sequences.",
    )
    parser.add_argument(
        "--test-video-count",
        type=int,
        default=3,
        help="Number of sorted test videos to export for qualitative checks.",
    )
    parser.add_argument(
        "--summary-json",
        default="vision_uav/runs/pipeline/formal_pipeline_summary.json",
        help="JSON summary output path.",
    )
    parser.add_argument(
        "--max-hours",
        type=float,
        default=12.0,
        help="Abort after probe if the estimated formal run exceeds this budget.",
    )
    return parser.parse_args()


def get_dataset_frame_counts(dataset_yaml_path: str | Path) -> dict[str, int]:
    dataset = load_yaml(resolve_workspace_path(dataset_yaml_path))
    dataset_root = Path(str(dataset["path"]))
    counts: dict[str, int] = {}
    for split in ("train", "val", "test"):
        image_dir = dataset_root / str(dataset[split])
        counts[split] = sum(1 for _ in image_dir.glob("*.jpg"))
    return counts


def estimate_training_time(probe_seconds: float, probe_fraction: float, probe_epochs: int, train_frames: int) -> dict[str, float]:
    probe_images = max(1.0, train_frames * probe_fraction)
    seconds_per_image = probe_seconds / max(1.0, probe_epochs * probe_images)
    return {
        "probe_seconds": probe_seconds,
        "seconds_per_image": seconds_per_image,
    }


def choose_formal_config(probe_result: dict, probe_duration: float, b8_config: str, b4_config: str) -> tuple[str, dict[str, float]]:
    config = probe_result["config"]
    train_frames = get_dataset_frame_counts(config["data"])["train"]
    estimate = estimate_training_time(
        probe_seconds=probe_duration,
        probe_fraction=float(config.get("fraction", 1.0)),
        probe_epochs=int(config.get("epochs", 1)),
        train_frames=train_frames,
    )
    b8 = load_yaml(resolve_workspace_path(b8_config))
    b4 = load_yaml(resolve_workspace_path(b4_config))
    b8_total_seconds = estimate["seconds_per_image"] * train_frames * int(b8["epochs"])
    b4_total_seconds = estimate["seconds_per_image"] * train_frames * int(b4["epochs"]) * (float(b8["batch"]) / float(b4["batch"]))
    estimate["b8_total_hours"] = b8_total_seconds / 3600.0
    estimate["b4_total_hours"] = b4_total_seconds / 3600.0
    return b8_config, estimate


def collect_test_videos(test_root: str | Path, limit: int) -> list[Path]:
    root = resolve_workspace_path(test_root)
    videos: list[Path] = []
    for sequence_dir in sorted(root.iterdir()):
        if not sequence_dir.is_dir():
            continue
        video_path = sequence_dir / "visible.mp4"
        if video_path.exists():
            videos.append(video_path)
        if len(videos) >= limit:
            break
    return videos


def main() -> int:
    args = parse_args()
    workspace_root_alias()
    data_root_alias()
    summary_path = resolve_workspace_path(args.summary_json)
    ensure_dir(summary_path.parent)

    started_at = time.time()
    probe_started = time.time()
    probe_result = run_train(args.probe_config)
    probe_duration = time.time() - probe_started
    selected_formal_config, estimate = choose_formal_config(
        probe_result,
        probe_duration,
        args.formal_config_b8,
        args.formal_config_b4,
    )

    summary = {
        "phase": args.phase,
        "probe": {
            "config": args.probe_config,
            "save_dir": str(probe_result["save_dir"]) if probe_result["save_dir"] else None,
            "duration_seconds": probe_duration,
        },
        "selected_formal_config": selected_formal_config,
        "estimate": estimate,
        "max_hours": args.max_hours,
        "started_at": started_at,
    }

    if args.phase == "probe":
        with summary_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    selected_hours_key = "b8_total_hours" if selected_formal_config == args.formal_config_b8 else "b4_total_hours"
    selected_hours = float(estimate[selected_hours_key])
    if selected_hours > args.max_hours:
        summary["aborted"] = {
            "reason": "estimated_budget_exceeded",
            "selected_hours": selected_hours,
        }
        with summary_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(summary, handle, indent=2, ensure_ascii=False)
        raise RuntimeError(
            f"Formal config {selected_formal_config} is estimated at {selected_hours:.2f}h, "
            f"which exceeds the configured {args.max_hours:.2f}h night budget."
        )

    formal_result = run_train(selected_formal_config)
    best_weights = Path(formal_result["save_dir"]) / "weights" / "best.pt"
    summary["formal"] = {
        "config": selected_formal_config,
        "save_dir": str(formal_result["save_dir"]) if formal_result["save_dir"] else None,
        "best_weights": str(best_weights),
    }

    eval_result = run_evaluation(args.eval_config, weights_override=str(best_weights))
    summary["test_metrics"] = eval_result["summary"]
    summary["test_eval_save_dir"] = str(eval_result["save_dir"]) if eval_result["save_dir"] else None

    infer_results = []
    test_videos = collect_test_videos(Path(args.test_root), args.test_video_count)
    for video_path in test_videos:
        sequence_name = video_path.parent.name
        infer_result = run_inference(
            args.infer_config,
            model_override=str(best_weights),
            source_override=str(video_path),
            source_id_override=sequence_name,
            name_override=f"formal_{sequence_name}",
            project_override="vision_uav/runs/infer/formal",
        )
        infer_results.append(
            {
                "sequence": sequence_name,
                "source": str(video_path),
                "output_root": str(infer_result["output_root"]),
                "overlay_mp4": str(infer_result["overlay_mp4"]),
                "predictions_jsonl": str(infer_result["predictions_jsonl"]),
            }
        )
    summary["inference_outputs"] = infer_results

    export_result = run_export(
        args.export_config,
        weights_override=str(best_weights),
        project_override="vision_uav/runs/export/formal",
        name_override=Path(formal_result["save_dir"]).name,
    )
    summary["onnx"] = {
        "output_root": str(export_result["output_root"]),
        "onnx_path": str(export_result["onnx_path"]),
    }
    summary["finished_at"] = time.time()
    summary["duration_hours"] = (summary["finished_at"] - started_at) / 3600.0

    with summary_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, indent=2, ensure_ascii=False)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
