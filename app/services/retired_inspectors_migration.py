"""Dry-run or back up and remove assets owned by the retired inspection tools."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
import stat
from pathlib import Path
import tempfile
import uuid


RETIRED_INSPECTORS = frozenset({
    "MembraneInspector", "ScratchedPipeItemInspector", "AirBubblesItemInspector",
})
RETIRED_WEIGHTS = (
    "yolo/segment_inner_permeable_membrane.pt",
    "yolo/segment_border_permeable_membrane.pt",
    "yolo/object_surface_detect.pt",
    "unet/detect_weld_line.pth",
)

def _is_link(path: Path) -> bool:
    return path.is_symlink() or bool(
        getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _read_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def _atomic_json(path: Path, data: dict) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=4)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def migrate_retired_inspectors(
    root: Path, backup_dir: Path, *, apply: bool = False, app_stopped: bool = False,
) -> dict:
    root = root.resolve(strict=True)
    if not (root / "app" / "storage").is_dir():
        raise ValueError(f"Not a project workspace: {root}")
    if apply and not app_stopped:
        raise ValueError("Stop the application and explicitly confirm app_stopped before applying.")
    storage = root / "app" / "storage"
    writes: dict[Path, dict] = {}
    removals: set[Path] = set()
    prune: set[Path] = set()
    removed_keys: list[str] = []
    law_path = storage / "config_judgment_law.json"
    if law_path.exists():
        original = _read_json(law_path)
        law = deepcopy(original)
        for product_id, frames in law.items():
            if not isinstance(frames, dict):
                raise ValueError(f"Invalid frame tree: {product_id}")
            for frame_id, items in frames.items():
                if not isinstance(items, dict):
                    raise ValueError(f"Invalid item tree: {product_id}/{frame_id}")
                for item_id, inspectors in items.items():
                    if not isinstance(inspectors, dict):
                        raise ValueError(f"Invalid inspector tree: {product_id}/{frame_id}/{item_id}")
                    for name in sorted(RETIRED_INSPECTORS.intersection(inspectors)):
                        del inspectors[name]
                        removed_keys.append(f"{product_id}/{frame_id}/{item_id}/{name}")
        if law != original:
            writes[law_path] = law

    config_path = storage / "config_software.json"
    config = _read_json(config_path) if config_path.exists() else {}
    clean_config = deepcopy(config)
    clean_config.pop("show_weld_skeleton", None)
    retrain_config = clean_config.get("retrain_inspectors", {})
    if not isinstance(retrain_config, dict):
        raise ValueError("Invalid retrain_inspectors configuration")
    for name in RETIRED_INSPECTORS:
        retrain_config.pop(name, None)
    if config != clean_config:
        writes[config_path] = clean_config

    for relative in RETIRED_WEIGHTS:
        candidate = root / "app" / "input" / "model" / relative
        if candidate.exists():
            removals.add(candidate)
    catalog = storage / "weld_reference_record.json"
    if catalog.exists():
        _read_json(catalog)
        removals.add(catalog)

    owned_dirs = [storage / "weld_reference"]
    output_roots = {root / "app" / "output"}
    configured_output = config.get("output_dir")
    if configured_output:
        configured = Path(configured_output)
        if not configured.is_absolute():
            configured = root / configured
        if configured.resolve() == Path(configured.anchor).resolve():
            raise ValueError("Refusing drive-root output directory")
        output_roots.add(configured)
    for output in output_roots:
        for inspector in RETIRED_INSPECTORS:
            owned_dirs.append(output / "retrain" / inspector)
    for directory in owned_dirs:
        if not directory.exists():
            continue
        if _is_link(directory):
            raise ValueError(f"Refusing linked data directory: {directory}")
        for candidate in directory.rglob("*"):
            if _is_link(candidate):
                raise ValueError(f"Refusing linked data: {candidate}")
            if candidate.is_file():
                removals.add(candidate)
            elif candidate.is_dir():
                prune.add(candidate)
        prune.add(directory)

    targets = sorted(set(writes) | removals, key=str)
    for path in targets:
        if _is_link(path) or not path.is_file():
            raise ValueError(f"Not an ordinary owned file: {path}")
        for parent in path.parents:
            if parent == root:
                break
            if _is_link(parent):
                raise ValueError(f"Refusing linked parent: {parent}")
    report = {
        "applied": False, "removed_config": removed_keys,
        "rewrite": [str(path) for path in writes],
        "remove": [str(path) for path in sorted(removals, key=str)],
        "backup": None,
    }
    if not apply or not targets and not prune:
        return report

    backup_dir = backup_dir.resolve()
    if backup_dir == root or backup_dir.is_relative_to(root):
        raise ValueError("Backup must be outside the workspace")
    for directory in owned_dirs:
        if backup_dir == directory.resolve() or backup_dir.is_relative_to(directory.resolve()):
            raise ValueError("Backup cannot be inside data being removed")
    destination = backup_dir / f"migration-{uuid.uuid4().hex}"
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    for index, path in enumerate(targets):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        copy_path = destination / f"{index:04d}-{path.name}"
        copy_path.write_bytes(data)
        if hashlib.sha256(copy_path.read_bytes()).hexdigest() != digest:
            raise OSError(f"Backup verification failed: {path}")
        entries.append({"source": str(path), "copy": copy_path.name, "sha256": digest})
    _atomic_json(destination / "manifest.json", {"workspace": str(root), "files": entries})
    for entry in entries:
        path = Path(entry["source"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise OSError(f"File changed during backup; nothing removed: {path}")
    report["backup"] = str(destination)
    for path, data in writes.items():
        _atomic_json(path, data)
    for path in sorted(removals, key=str):
        path.unlink()
    for directory in sorted(prune, key=lambda path: len(path.parts), reverse=True):
        directory.rmdir()
    report["applied"] = True
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--backup", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--app-stopped", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate_retired_inspectors(
        args.root, args.backup, apply=args.apply, app_stopped=args.app_stopped,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
