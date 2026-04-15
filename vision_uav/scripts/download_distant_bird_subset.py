#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import zipfile
from collections import Counter
from pathlib import Path

import gdown

from common import ensure_dir, load_yaml, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download a compact public subset of the Distant Bird Detection dataset."
    )
    parser.add_argument(
        "--config",
        default="vision_uav/configs/distant_bird_subset.yaml",
        help="Path to the distant-bird subset YAML config.",
    )
    return parser.parse_args()


def load_annotations(raw_root: Path, file_id: str) -> tuple[list[dict], list[dict], Path]:
    archive_path = raw_root / "annotations.zip"
    if not archive_path.exists():
        gdown.download(id=file_id, output=str(archive_path), quiet=False)

    extract_root = ensure_dir(raw_root / "annotations")
    train_path = extract_root / "annotations" / "train.json"
    val_path = extract_root / "annotations" / "val.json"
    if not train_path.exists() or not val_path.exists():
        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extract_root)

    train_rows = json.loads(train_path.read_text(encoding="utf-8"))
    val_rows = json.loads(val_path.read_text(encoding="utf-8"))
    return train_rows, val_rows, extract_root


def list_drive_archives(folder_url: str) -> dict[str, object]:
    files = gdown.download_folder(url=folder_url, output=None, quiet=True, skip_download=True)
    mapping: dict[str, object] = {}
    for item in files or []:
        name = Path(item.path).name
        mapping[name] = item
    return mapping


def select_folders(rows: list[dict], target_images: int, minimum_folders: int) -> list[str]:
    counts = Counter(str(row["path"]).split("/")[0] for row in rows)
    chosen: list[str] = []
    running = 0
    for folder_name, count in counts.most_common():
        chosen.append(folder_name)
        running += int(count)
        if running >= target_images and len(chosen) >= minimum_folders:
            break
    return chosen


def download_archives(raw_root: Path, archive_map: dict[str, object], folder_ids: list[str]) -> list[Path]:
    archives_dir = ensure_dir(raw_root / "images_archives")
    downloaded: list[Path] = []
    for folder_id in folder_ids:
        archive_name = f"{folder_id}.zip"
        item = archive_map.get(archive_name)
        if item is None:
            raise FileNotFoundError(f"Archive {archive_name} not found in Google Drive folder listing.")
        destination = archives_dir / archive_name
        if not destination.exists():
            gdown.download(id=item.id, output=str(destination), quiet=False)
        downloaded.append(destination)
    return downloaded


def extract_archives(raw_root: Path, archives: list[Path]) -> Path:
    extracted_root = ensure_dir(raw_root / "images_extracted")
    for archive in archives:
        folder_name = archive.stem
        marker_dir = extracted_root / folder_name
        if marker_dir.exists():
            continue
        with zipfile.ZipFile(archive, "r") as zf:
            zf.extractall(extracted_root)
    return extracted_root


def sample_rows(rows: list[dict], selected_folders: list[str], target_images: int) -> list[dict]:
    chosen_rows = [row for row in rows if str(row["path"]).split("/")[0] in selected_folders]
    chosen_rows.sort(key=lambda row: (str(row["path"]).split("/")[0], str(row["path"])))
    return chosen_rows[:target_images]


def materialize_images(
    extracted_root: Path,
    sampled_rows: list[dict],
    output_dir: Path,
    manifest_name: str,
) -> dict:
    ensure_dir(output_dir)
    copied = 0
    missing: list[str] = []
    images_manifest: list[dict] = []
    for row in sampled_rows:
        relative_path = Path(str(row["path"]))
        source_path = extracted_root / relative_path
        if not source_path.exists():
            missing.append(str(relative_path).replace("\\", "/"))
            continue
        destination_name = f"{relative_path.parent.name}_{relative_path.name}"
        destination_path = output_dir / destination_name
        if not destination_path.exists():
            destination_path.write_bytes(source_path.read_bytes())
        copied += 1
        images_manifest.append(
            {
                "source_path": str(relative_path).replace("\\", "/"),
                "local_name": destination_name,
                "object_count": len(row.get("bbox", [])),
                "labels": row.get("label", []),
            }
        )

    summary = {
        "manifest_name": manifest_name,
        "output_dir": str(output_dir),
        "copied_images": copied,
        "missing_images": missing,
        "images": images_manifest,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    raw_root = ensure_dir(resolve_workspace_path(config["raw_output_root"]))
    processed_root = ensure_dir(resolve_workspace_path(config["processed_output_root"]))

    train_rows, val_rows, annotations_root = load_annotations(raw_root, str(config["annotations_file_id"]))
    archive_map = list_drive_archives(str(config["images_folder_url"]))

    train_folders = select_folders(
        train_rows,
        target_images=int(config["train_target_images"]),
        minimum_folders=int(config.get("min_train_folders", 1)),
    )
    val_folders = select_folders(
        val_rows,
        target_images=int(config["val_target_images"]),
        minimum_folders=int(config.get("min_val_folders", 1)),
    )
    all_folders = sorted(set(train_folders + val_folders), key=lambda value: int(value))

    archives = download_archives(raw_root, archive_map, all_folders)
    extracted_root = extract_archives(raw_root, archives)

    sampled_train_rows = sample_rows(train_rows, train_folders, int(config["train_target_images"]))
    sampled_val_rows = sample_rows(val_rows, val_folders, int(config["val_target_images"]))

    train_summary = materialize_images(
        extracted_root,
        sampled_train_rows,
        ensure_dir(processed_root / str(config["train_pool_name"]) / "images"),
        manifest_name=str(config["train_pool_name"]),
    )
    eval_summary = materialize_images(
        extracted_root,
        sampled_val_rows,
        ensure_dir(processed_root / str(config["eval_suite_name"]) / "images"),
        manifest_name=str(config["eval_suite_name"]),
    )

    overall_summary = {
        "annotations_root": str(annotations_root),
        "selected_train_folders": train_folders,
        "selected_val_folders": val_folders,
        "downloaded_archives": [str(path) for path in archives],
        "train_pool": train_summary,
        "eval_suite": eval_summary,
    }
    summary_path = raw_root / "subset_summary.json"
    summary_path.write_text(json.dumps(overall_summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"raw_root={raw_root}")
    print(f"summary_json={summary_path}")
    print(json.dumps(overall_summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
