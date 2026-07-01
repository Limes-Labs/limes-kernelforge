from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path
from typing import Any

from harness.submission_guard import normalize_path, validate_changed_paths


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1.0"
BUNDLE_KIND = "editable-source-bundle"


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "bundle_sha256"}
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _path_inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _file_record(root: Path, relative_path: str) -> tuple[dict[str, Any] | None, list[str]]:
    target = root / relative_path
    errors: list[str] = []
    if not _path_inside_root(target, root):
        return None, [f"changed file escapes repository root: {relative_path}"]
    if target.is_symlink():
        return None, [f"changed file must not be a symlink: {relative_path}"]
    if not target.exists():
        return None, [f"changed file does not exist: {relative_path}"]
    if not target.is_file():
        return None, [f"changed path is not a regular file: {relative_path}"]

    data = target.read_bytes()
    mode = stat.S_IMODE(target.stat().st_mode)
    record = {
        "path": relative_path,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "executable": bool(mode & 0o111),
    }
    return record, errors


def build_source_bundle(
    contract: dict[str, Any],
    changed_paths: list[str],
    source_commit: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    normalized = [normalize_path(path) for path in changed_paths if normalize_path(path)]
    errors = validate_changed_paths(normalized, contract)
    if len(set(normalized)) != len(normalized):
        errors.append("changed files must not contain duplicates")

    file_records: list[dict[str, Any]] = []
    for relative_path in sorted(set(normalized)):
        record, file_errors = _file_record(root, relative_path)
        errors.extend(file_errors)
        if record is not None:
            file_records.append(record)

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "challenge": contract.get("id"),
        "bundle_kind": BUNDLE_KIND,
        "source_commit": source_commit,
        "changed_files": [record["path"] for record in file_records],
        "file_count": len(file_records),
        "total_size_bytes": sum(record["size_bytes"] for record in file_records),
        "files": file_records,
    }
    bundle["bundle_sha256"] = canonical_digest(bundle)
    return {
        "ok": not errors,
        "challenge": contract.get("id"),
        "bundle": bundle,
        "errors": errors,
    }


def validate_source_bundle(
    bundle: dict[str, Any],
    contract: dict[str, Any],
    root: Path = ROOT,
    changed_paths: list[str] | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    for field, expected in [
        ("schema_version", SCHEMA_VERSION),
        ("challenge", contract.get("id")),
        ("bundle_kind", BUNDLE_KIND),
    ]:
        if bundle.get(field) != expected:
            errors.append(f"source bundle {field} must be {expected!r}")

    expected_digest = canonical_digest(bundle)
    if bundle.get("bundle_sha256") != expected_digest:
        errors.append("source bundle bundle_sha256 does not match its canonical payload")

    bundle_paths = bundle.get("changed_files")
    if not isinstance(bundle_paths, list) or not all(isinstance(path, str) for path in bundle_paths):
        errors.append("source bundle changed_files must be a list of paths")
        bundle_paths = []
    paths = changed_paths if changed_paths is not None else bundle_paths
    commit = source_commit if source_commit is not None else bundle.get("source_commit")
    if not isinstance(commit, str) or not commit.strip() or commit.strip().startswith("<"):
        errors.append("source bundle source_commit must be concrete")
        commit = ""

    current = build_source_bundle(contract, list(paths), commit, root)
    errors.extend(current["errors"])
    current_bundle = current["bundle"]
    if bundle != current_bundle:
        errors.append("source bundle is stale or does not match current editable files")

    return {
        "ok": not errors,
        "challenge": contract.get("id"),
        "bundle_sha256": bundle.get("bundle_sha256"),
        "expected_bundle_sha256": current_bundle.get("bundle_sha256"),
        "changed_files": current_bundle.get("changed_files", []),
        "file_count": current_bundle.get("file_count", 0),
        "errors": errors,
    }


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
