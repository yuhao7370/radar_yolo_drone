#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import onnxruntime as ort

from common import ensure_dir, load_yaml, load_yolo_model, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a trained YOLO model to ONNX and validate it.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/export_onnx.yaml",
        help="Path to the ONNX export YAML config.",
    )
    parser.add_argument("--weights", default=None, help="Optional explicit weights override.")
    return parser.parse_args()


def validate_export(onnx_path: Path, imgsz: int) -> None:
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    dummy = np.zeros((1, 3, imgsz, imgsz), dtype=np.float32)
    outputs = session.run(None, {input_name: dummy})
    print(f"onnx_input={input_name}")
    print(f"onnx_outputs={len(outputs)}")


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    weights_path = str(resolve_workspace_path(args.weights or str(config["weights"])))
    fallback_model = config.get("fallback_model")
    output_root = ensure_dir(resolve_workspace_path(str(config["project"]))) / str(config["name"])
    ensure_dir(output_root)
    imgsz = int(config.get("imgsz", 1280))

    model = load_yolo_model(weights_path, str(fallback_model) if fallback_model else None)
    exported = model.export(
        format="onnx",
        imgsz=imgsz,
        dynamic=bool(config.get("dynamic", False)),
        simplify=bool(config.get("simplify", True)),
        device=config.get("device", 0),
        project=str(output_root.parent),
        name=output_root.name,
    )
    onnx_path = Path(exported)
    validate_export(onnx_path, imgsz)
    print(f"onnx_path={onnx_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
