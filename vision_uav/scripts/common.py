from __future__ import annotations

import os
from pathlib import Path
from contextlib import contextmanager
from typing import Any

import yaml
from ultralytics import YOLO


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected a mapping in YAML file: {path}")
    return data


def dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def resolve_workspace_path(value: str | Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    return workspace_root().parent / candidate


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def pretrained_weights_dir() -> Path:
    return ensure_dir(workspace_root() / "weights" / "pretrained")


@contextmanager
def pushd(path: Path):
    previous = Path.cwd()
    ensure_dir(path)
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


def is_plain_model_name(model_ref: str) -> bool:
    path = Path(model_ref)
    if path.is_absolute():
        return False
    if any(sep in model_ref for sep in ("/", "\\")):
        return False
    return model_ref.endswith(".pt")


def load_yolo_model(model_ref: str, fallback_model: str | None = None) -> YOLO:
    def _instantiate(ref: str) -> YOLO:
        if is_plain_model_name(ref):
            with pushd(pretrained_weights_dir()):
                return YOLO(ref)
        return YOLO(str(resolve_workspace_path(ref)))

    try:
        return _instantiate(model_ref)
    except Exception:
        if fallback_model is None:
            raise
        print(f"primary_model_failed={model_ref}")
        print(f"fallback_model={fallback_model}")
        return _instantiate(fallback_model)
