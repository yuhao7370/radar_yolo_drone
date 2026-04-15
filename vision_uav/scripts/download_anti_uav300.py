#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import requests

from common import ensure_dir, load_yaml, resolve_workspace_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and optionally extract Anti-UAV300.")
    parser.add_argument(
        "--config",
        default="vision_uav/configs/download_anti_uav300.yaml",
        help="Path to the download config YAML.",
    )
    parser.add_argument("--skip-extract", action="store_true", help="Only download the ZIP file.")
    parser.add_argument("--force", action="store_true", help="Re-download even if the ZIP already exists.")
    return parser.parse_args()


def format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def download_file(url: str, destination: Path, expected_size: int | None, force: bool) -> None:
    if destination.exists() and not force:
        current_size = destination.stat().st_size
        if expected_size is None or current_size == expected_size:
            print(f"zip_exists={destination}")
            print(f"zip_size={current_size}")
            return
        print(f"zip_size_mismatch={current_size}, expected={expected_size}, re_downloading=true")

    ensure_dir(destination.parent)
    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", "0")) or expected_size or 0
        downloaded = 0
        chunk_size = 8 * 1024 * 1024
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if not chunk:
                    continue
                handle.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = (downloaded / total) * 100.0
                    print(
                        f"\rdownloaded={format_size(downloaded)} / {format_size(total)} "
                        f"({percent:5.1f}%)",
                        end="",
                        flush=True,
                    )
                else:
                    print(f"\rdownloaded={format_size(downloaded)}", end="", flush=True)
        print()

    actual_size = destination.stat().st_size
    print(f"zip_path={destination}")
    print(f"zip_size={actual_size}")
    if expected_size is not None and actual_size != expected_size:
        raise RuntimeError(f"Downloaded file size mismatch: got {actual_size}, expected {expected_size}")


def extract_zip(zip_path: Path, extract_root: Path) -> None:
    ensure_dir(extract_root)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        root_names = sorted({name.split('/')[0] for name in names if name and not name.startswith('__MACOSX/')})
        print(f"archive_top_level={root_names[:10]}")
        archive.extractall(extract_root)
    print(f"extract_root={extract_root}")


def main() -> int:
    args = parse_args()
    config = load_yaml(resolve_workspace_path(args.config))
    url = str(config["url"])
    zip_path = resolve_workspace_path(str(config["zip_path"]))
    extract_root = resolve_workspace_path(str(config["extract_root"]))
    expected_size = config.get("expected_size")
    expected = int(expected_size) if expected_size is not None else None

    download_file(url, zip_path, expected, args.force)
    if not args.skip_extract:
        extract_zip(zip_path, extract_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
