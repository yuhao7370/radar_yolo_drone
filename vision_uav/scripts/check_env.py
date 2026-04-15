#!/usr/bin/env python
from __future__ import annotations

import argparse
import importlib
import sys

from common import load_yolo_model
REQUIRED_MODULES = ["torch", "ultralytics", "cv2", "onnx", "onnxruntime", "yaml"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the vision_uav runtime environment.")
    parser.add_argument(
        "--smoke-model",
        default="yolo26n.pt",
        help="Model name used for a minimal Ultralytics load test.",
    )
    return parser.parse_args()


def import_required_modules() -> dict[str, object]:
    loaded = {}
    for name in REQUIRED_MODULES:
        module = importlib.import_module(name)
        loaded[name] = module
    return loaded


def main() -> int:
    args = parse_args()
    modules = import_required_modules()
    torch = modules["torch"]
    print(f"python={sys.version.split()[0]}")
    print(f"torch={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")
    print(f"cuda_device_count={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        print(f"cuda_device_name={torch.cuda.get_device_name(0)}")

    model = load_yolo_model(args.smoke_model)
    print(f"smoke_model={args.smoke_model}")
    print(f"model_task={model.task}")
    print("environment_check=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
