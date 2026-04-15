#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Iterable

import cv2

from common import ensure_dir, load_yaml, load_yolo_model, resolve_workspace_path


IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run offline inference and write overlay.mp4 + predictions.jsonl.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/infer_video.yaml",
        help="Path to the inference YAML config.",
    )
    parser.add_argument("--model", default=None, help="Optional explicit model override.")
    parser.add_argument("--source", default=None, help="Optional explicit source override.")
    parser.add_argument("--source-id", default=None, help="Optional explicit source_id override.")
    parser.add_argument("--name", default=None, help="Optional explicit output name override.")
    parser.add_argument("--project", default=None, help="Optional explicit output project override.")
    return parser.parse_args()


def iter_image_paths(image_dir: Path) -> list[Path]:
    return sorted([path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES])


def detections_from_result(result) -> list[dict[str, object]]:
    detections: list[dict[str, object]] = []
    boxes = getattr(result, "boxes", None)
    names = getattr(result, "names", {})
    if boxes is None:
        return detections

    xyxy = boxes.xyxy.cpu().tolist()
    confs = boxes.conf.cpu().tolist()
    classes = boxes.cls.cpu().tolist()
    for coords, confidence, class_id in zip(xyxy, confs, classes):
        numeric_class = int(class_id)
        detections.append(
            {
                "bbox_xyxy": [round(float(value), 4) for value in coords],
                "class_id": numeric_class,
                "class_name": str(names.get(numeric_class, numeric_class)),
                "confidence": round(float(confidence), 6),
            }
        )
    return detections


def open_writer(path: Path, fps: float, frame_width: int, frame_height: int) -> cv2.VideoWriter:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (frame_width, frame_height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open video writer: {path}")
    return writer


def infer_on_frames(
    model: YOLO,
    frames: Iterable[tuple[int, float, any]],
    output_root: Path,
    source_id: str,
    fps: float,
    imgsz: int,
    conf: float,
    device: int | str,
) -> None:
    jsonl_path = output_root / "predictions.jsonl"
    writer: cv2.VideoWriter | None = None

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as jsonl_file:
        for frame_id, timestamp_ms, frame in frames:
            result = model.predict(source=frame, imgsz=imgsz, conf=conf, device=device, verbose=False)[0]
            detections = detections_from_result(result)
            overlay = result.plot()
            frame_height, frame_width = frame.shape[:2]
            if writer is None:
                writer = open_writer(output_root / "overlay.mp4", fps, frame_width, frame_height)
            writer.write(overlay)
            payload = {
                "source_id": source_id,
                "frame_id": frame_id,
                "timestamp_ms": round(float(timestamp_ms), 3),
                "width": int(frame_width),
                "height": int(frame_height),
                "detections": detections,
            }
            jsonl_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    if writer is not None:
        writer.release()


def infer_video_source(
    model: YOLO,
    source: Path,
    output_root: Path,
    source_id: str,
    imgsz: int,
    conf: float,
    device: int | str,
) -> None:
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise RuntimeError(f"Failed to open source video: {source}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 10.0

    def frame_iter():
        frame_id = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp_ms = capture.get(cv2.CAP_PROP_POS_MSEC)
            yield frame_id, timestamp_ms, frame
            frame_id += 1

    try:
        infer_on_frames(model, frame_iter(), output_root, source_id, fps, imgsz, conf, device)
    finally:
        capture.release()


def infer_image_dir_source(
    model: YOLO,
    source: Path,
    output_root: Path,
    source_id: str,
    fps: float,
    imgsz: int,
    conf: float,
    device: int | str,
) -> None:
    image_paths = iter_image_paths(source)
    if not image_paths:
        raise ValueError(f"No images found under {source}")

    def frame_iter():
        for frame_id, image_path in enumerate(image_paths):
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise RuntimeError(f"Failed to read image: {image_path}")
            timestamp_ms = (frame_id / fps) * 1000.0
            yield frame_id, timestamp_ms, frame

    infer_on_frames(model, frame_iter(), output_root, source_id, fps, imgsz, conf, device)


def infer_camera_source(
    model: YOLO,
    camera_index: int,
    output_root: Path,
    source_id: str,
    fps: float,
    imgsz: int,
    conf: float,
    device: int | str,
) -> None:
    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Failed to open camera index: {camera_index}")

    def frame_iter():
        frame_id = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame_id, time.time() * 1000.0, frame
            frame_id += 1

    try:
        infer_on_frames(model, frame_iter(), output_root, source_id, fps, imgsz, conf, device)
    finally:
        capture.release()


def run_inference(
    config_path: str | Path,
    model_override: str | None = None,
    source_override: str | None = None,
    source_id_override: str | None = None,
    name_override: str | None = None,
    project_override: str | None = None,
) -> dict[str, Any]:
    config = load_yaml(resolve_workspace_path(config_path))
    source_value = source_override or str(config["source"])
    model_name = model_override or str(config["model"])
    fallback_model = config.get("fallback_model")
    project_value = project_override or str(config["project"])
    name_value = name_override or str(config["name"])
    project_root = ensure_dir(resolve_workspace_path(project_value))
    output_root = ensure_dir(project_root / name_value)
    source_id = str(source_id_override or config.get("source_id", Path(source_value).stem or "camera"))
    fps = float(config.get("fps", 10.0))
    imgsz = int(config.get("imgsz", 1280))
    conf = float(config.get("conf", 0.25))
    device = config.get("device", 0)

    model = load_yolo_model(model_name, str(fallback_model) if fallback_model else None)

    if source_value.isdigit():
        infer_camera_source(model, int(source_value), output_root, source_id, fps, imgsz, conf, device)
    else:
        source_path = resolve_workspace_path(source_value)
        if source_path.is_dir():
            infer_image_dir_source(model, source_path, output_root, source_id, fps, imgsz, conf, device)
        else:
            infer_video_source(model, source_path, output_root, source_id, imgsz, conf, device)

    return {
        "config": config,
        "output_root": output_root,
        "overlay_mp4": output_root / "overlay.mp4",
        "predictions_jsonl": output_root / "predictions.jsonl",
        "source_id": source_id,
    }


def main() -> int:
    args = parse_args()
    result = run_inference(
        args.config,
        model_override=args.model,
        source_override=args.source,
        source_id_override=args.source_id,
        name_override=args.name,
        project_override=args.project,
    )
    print(f"output_root={result['output_root']}")
    print(f"overlay_mp4={result['overlay_mp4']}")
    print(f"predictions_jsonl={result['predictions_jsonl']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
