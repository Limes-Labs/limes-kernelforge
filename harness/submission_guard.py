from __future__ import annotations

import json
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


ALLOWED_SUBMISSION_STATUSES = {"local", "candidate"}
ALLOWED_PRIMITIVES = {"rmsnorm", "rope", "attention", "kv_decode"}
REQUIRED_PUBLIC_SCORE_FIELDS = {
    "correct",
    "primary_correct",
    "max_abs_error",
    "max_rel_error",
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_runtime_delta_ms",
    "public_speedup_vs_reference",
    "public_stress_correct",
    "public_stress_case_count",
    "public_stress_max_abs_error",
    "public_stress_max_rel_error",
    "public_stress_geomean_runtime_ms",
    "reference_public_stress_geomean_runtime_ms",
    "public_stress_speedup_vs_reference",
    "backend",
    "tolerance",
}
REQUIRED_INVARIANT_PROBE_FIELDS = {"ok", "probe_count"}
REQUIRED_SEARCH_LEDGER_FIELDS = {"path", "validated"}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip("/")


def path_matches(path: str, pattern: str) -> bool:
    normalized = normalize_path(path)
    pattern = normalize_path(pattern)
    if pattern.endswith("/**"):
        return normalized.startswith(pattern[:-2])
    return fnmatch(normalized, pattern)


def classify_changed_paths(changed_paths: list[str], contract: dict[str, Any]) -> dict[str, list[str]]:
    editable_patterns = list(contract.get("editablePaths", []))
    forbidden_patterns = list(contract.get("forbiddenPaths", []))
    classified = {
        "editable": [],
        "forbidden": [],
        "unknown": [],
    }
    for raw_path in changed_paths:
        path = normalize_path(raw_path)
        if not path:
            continue
        if any(path_matches(path, pattern) for pattern in forbidden_patterns):
            classified["forbidden"].append(path)
        elif any(path_matches(path, pattern) for pattern in editable_patterns):
            classified["editable"].append(path)
        else:
            classified["unknown"].append(path)
    return classified


def validate_changed_paths(changed_paths: list[str], contract: dict[str, Any]) -> list[str]:
    classified = classify_changed_paths(changed_paths, contract)
    errors: list[str] = []
    if classified["forbidden"]:
        errors.append(
            "forbidden files changed: " + ", ".join(sorted(classified["forbidden"]))
        )
    if classified["unknown"]:
        errors.append(
            "files outside editable surface changed: " + ", ".join(sorted(classified["unknown"]))
        )
    if not classified["editable"]:
        errors.append("no editable submission files were changed")
    return errors


def _looks_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return not stripped or stripped.startswith("<") or "Short description" in stripped


def _validate_invariant_probes(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["manifest invariant_probes must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_INVARIANT_PROBE_FIELDS.difference(value))
    if missing:
        errors.append("manifest invariant_probes missing fields: " + ", ".join(missing))
    if value.get("ok") is not True:
        errors.append("manifest invariant_probes.ok must be true")
    if not isinstance(value.get("probe_count"), int) or value["probe_count"] < 4:
        errors.append("manifest invariant_probes.probe_count must be an integer >= 4")
    return errors


def _validate_search_ledger(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return ["manifest search_ledger must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_SEARCH_LEDGER_FIELDS.difference(value))
    if missing:
        errors.append("manifest search_ledger missing fields: " + ", ".join(missing))
    if _looks_placeholder(value.get("path")):
        errors.append("manifest search_ledger.path must be concrete")
    if value.get("validated") is not True:
        errors.append("manifest search_ledger.validated must be true")
    return errors


def validate_manifest(manifest: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if manifest.get("challenge") != contract.get("id"):
        errors.append("manifest challenge does not match challenge.json id")
    if manifest.get("status") not in ALLOWED_SUBMISSION_STATUSES:
        errors.append("manifest status must be local or candidate before trusted replay")
    if _looks_placeholder(manifest.get("commit")):
        errors.append("manifest commit must be a concrete commit SHA")

    changed_files = manifest.get("changed_files")
    if not isinstance(changed_files, list) or not all(isinstance(item, str) for item in changed_files):
        errors.append("manifest changed_files must be a list of paths")
        changed_files = []
    else:
        errors.extend(validate_changed_paths(changed_files, contract))

    primitives = manifest.get("primitives")
    if not isinstance(primitives, list) or not primitives:
        errors.append("manifest primitives must be a non-empty list")
    else:
        unknown = sorted(set(primitives).difference(ALLOWED_PRIMITIVES))
        if unknown:
            errors.append("manifest primitives contains unknown entries: " + ", ".join(unknown))

    public_score = manifest.get("public_score")
    if not isinstance(public_score, dict):
        errors.append("manifest public_score must be an object")
    else:
        missing = sorted(REQUIRED_PUBLIC_SCORE_FIELDS.difference(public_score))
        if missing:
            errors.append("manifest public_score missing fields: " + ", ".join(missing))
        if public_score.get("correct") is not True:
            errors.append("manifest public_score.correct must be true for candidate replay")
        if public_score.get("primary_correct") is not True:
            errors.append("manifest public_score.primary_correct must be true for candidate replay")
        if public_score.get("public_stress_correct") is not True:
            errors.append("manifest public_score.public_stress_correct must be true for candidate replay")
        if "public_stress_case_count" in public_score and (
            not isinstance(public_score["public_stress_case_count"], int)
            or public_score["public_stress_case_count"] < 4
        ):
            errors.append("manifest public_score.public_stress_case_count must be an integer >= 4")

    errors.extend(_validate_invariant_probes(manifest.get("invariant_probes")))
    errors.extend(_validate_search_ledger(manifest.get("search_ledger")))

    if _looks_placeholder(manifest.get("hardware_fingerprint")):
        errors.append("manifest hardware_fingerprint must describe the local machine")
    if not isinstance(manifest.get("native_extension"), bool):
        errors.append("manifest native_extension must be a boolean")
    if _looks_placeholder(manifest.get("method_summary")):
        errors.append("manifest method_summary must describe the submitted kernel idea")
    failure_modes = manifest.get("expected_failure_modes")
    if not isinstance(failure_modes, list) or not failure_modes:
        errors.append("manifest expected_failure_modes must be a non-empty list")
    elif any(_looks_placeholder(item) for item in failure_modes):
        errors.append("manifest expected_failure_modes must not contain placeholders")
    return errors


def validate_submission(
    manifest: dict[str, Any],
    contract: dict[str, Any],
    changed_paths: list[str] | None = None,
) -> list[str]:
    errors = validate_manifest(manifest, contract)
    if changed_paths is None:
        return errors

    normalized_manifest_paths = sorted(normalize_path(path) for path in manifest.get("changed_files", []))
    normalized_changed_paths = sorted(normalize_path(path) for path in changed_paths)
    errors.extend(validate_changed_paths(normalized_changed_paths, contract))
    if normalized_manifest_paths != normalized_changed_paths:
        errors.append("manifest changed_files must exactly match the checked git diff")
    return errors
