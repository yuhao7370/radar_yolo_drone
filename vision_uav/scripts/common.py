from __future__ import annotations

import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import yaml
from ultralytics import YOLO

WORKSPACE_ALIAS = Path("C:/vision_uav_workspace")
DATA_ALIAS = Path("C:/vision_uav_data")


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


def ensure_junction(alias: Path, target: Path) -> Path:
    alias = Path(os.path.abspath(alias))
    target = target.resolve()
    if alias.exists():
        return alias
    ensure_dir(alias.parent)
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0 and not alias.exists():
        raise RuntimeError(
            f"Failed to create junction {alias} -> {target}: "
            f"{completed.stdout.strip()} {completed.stderr.strip()}".strip()
        )
    return alias


def workspace_root_alias() -> Path:
    if os.name != "nt":
        return workspace_root()
    return ensure_junction(WORKSPACE_ALIAS, workspace_root())


def data_root_alias() -> Path:
    if os.name != "nt":
        return workspace_root() / "data"
    return ensure_junction(DATA_ALIAS, workspace_root() / "data")


def resolve_workspace_path(value: str | Path) -> Path:
    candidate = Path(value)
    if candidate.is_absolute():
        return candidate
    if candidate.parts and candidate.parts[0] == workspace_root().name:
        alias = workspace_root_alias()
        return alias.joinpath(*candidate.parts[1:])
    return workspace_root().parent / candidate


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def pretrained_weights_dir() -> Path:
    return ensure_dir(workspace_root_alias() / "weights" / "pretrained")


def reset_dir(path: Path) -> Path:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


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


def extract_detection_metrics(metrics) -> dict[str, float]:
    box = metrics.box
    return {
        "precision": float(box.p.mean() if hasattr(box.p, "mean") else box.p),
        "recall": float(box.r.mean() if hasattr(box.r, "mean") else box.r),
        "mAP50": float(box.map50),
        "mAP50-95": float(box.map),
    }
