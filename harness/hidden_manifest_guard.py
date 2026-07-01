from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1.0"
CHALLENGE = "limes-kernelforge"
MANIFEST_KIND = "trusted-hidden-case-manifest"
HASH_ALGORITHM = "sha256"
PRIMITIVES = {"rmsnorm", "rope", "attention", "kv_decode"}
DTYPES = {"float64", "float32", "float16", "bfloat16"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "manifest_kind",
    "source",
    "hidden_manifest_ready",
    "hash_algorithm",
    "case_policy",
    "case_suites",
    "runner_tracks",
    "tolerance_matrix_hash",
    "timing_policy_hash",
}
REQUIRED_CASE_POLICY = {
    "candidate_selection_uses_hidden_cases",
    "hidden_shapes_disclosed_to_candidates",
    "fixed_runner_feedback_before_freeze",
}
REQUIRED_CASE_SUITE = {
    "id",
    "primitive",
    "dtype",
    "shape_class",
    "case_count",
    "sha256",
    "disclosed_to_candidates",
}
REQUIRED_RUNNER_TRACK = {
    "id",
    "status",
    "hardware_fingerprint_sha256",
    "disclosed_to_candidates",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_example(payload: dict[str, Any]) -> bool:
    return payload.get("source") == "example-schema-only"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _looks_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value.lower()
    )


def _missing(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _validate_hash_field(payload: dict[str, Any], field: str, example: bool) -> list[str]:
    if example:
        if not _non_empty_string(payload.get(field)):
            return [f"{field} must be a non-empty string"]
    elif not _looks_sha256(payload.get(field)):
        return [f"{field} must be a sha256 hex string"]
    return []


def _validate_case_policy(policy: Any) -> list[str]:
    if not isinstance(policy, dict):
        return ["case_policy must be an object"]
    errors: list[str] = []
    missing = _missing(policy, REQUIRED_CASE_POLICY)
    if missing:
        errors.append("case_policy missing fields: " + ", ".join(missing))
        return errors
    if policy.get("candidate_selection_uses_hidden_cases") is not False:
        errors.append("case_policy.candidate_selection_uses_hidden_cases must be false")
    if policy.get("hidden_shapes_disclosed_to_candidates") is not False:
        errors.append("case_policy.hidden_shapes_disclosed_to_candidates must be false")
    if policy.get("fixed_runner_feedback_before_freeze") is not False:
        errors.append("case_policy.fixed_runner_feedback_before_freeze must be false")
    return errors


def _validate_case_suites(case_suites: Any, example: bool) -> list[str]:
    if not isinstance(case_suites, list) or not case_suites:
        return ["case_suites must be a non-empty list"]
    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_primitives: set[str] = set()
    for index, suite in enumerate(case_suites):
        prefix = f"case_suites[{index}]"
        if not isinstance(suite, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = _missing(suite, REQUIRED_CASE_SUITE)
        if missing:
            errors.append(f"{prefix} missing fields: " + ", ".join(missing))
            continue
        suite_id = suite.get("id")
        if not _non_empty_string(suite_id):
            errors.append(f"{prefix}.id must be a non-empty string")
        elif suite_id in seen_ids:
            errors.append(f"{prefix}.id duplicates an earlier case suite")
        else:
            seen_ids.add(suite_id)
        primitive = suite.get("primitive")
        if primitive not in PRIMITIVES:
            errors.append(f"{prefix}.primitive must be one of {sorted(PRIMITIVES)}")
        else:
            seen_primitives.add(primitive)
        if suite.get("dtype") not in DTYPES:
            errors.append(f"{prefix}.dtype must be one of {sorted(DTYPES)}")
        if not _non_empty_string(suite.get("shape_class")):
            errors.append(f"{prefix}.shape_class must be a non-empty string")
        if example:
            if not isinstance(suite.get("case_count"), int) or suite["case_count"] < 0:
                errors.append(f"{prefix}.case_count must be a non-negative integer")
        elif not isinstance(suite.get("case_count"), int) or suite["case_count"] <= 0:
            errors.append(f"{prefix}.case_count must be a positive integer")
        if example:
            if not _non_empty_string(suite.get("sha256")):
                errors.append(f"{prefix}.sha256 must be a non-empty string")
        elif not _looks_sha256(suite.get("sha256")):
            errors.append(f"{prefix}.sha256 must be a sha256 hex string")
        if suite.get("disclosed_to_candidates") is not False:
            errors.append(f"{prefix}.disclosed_to_candidates must be false")
    missing_primitives = sorted(PRIMITIVES - seen_primitives)
    if missing_primitives:
        errors.append("case_suites must include every primitive: " + ", ".join(missing_primitives))
    return errors


def _validate_runner_tracks(runner_tracks: Any, replay_contract: dict[str, Any], example: bool) -> list[str]:
    if not isinstance(runner_tracks, list) or not runner_tracks:
        return ["runner_tracks must be a non-empty list"]
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, track in enumerate(runner_tracks):
        prefix = f"runner_tracks[{index}]"
        if not isinstance(track, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = _missing(track, REQUIRED_RUNNER_TRACK)
        if missing:
            errors.append(f"{prefix} missing fields: " + ", ".join(missing))
            continue
        track_id = track.get("id")
        if not _non_empty_string(track_id):
            errors.append(f"{prefix}.id must be a non-empty string")
        elif track_id in seen_ids:
            errors.append(f"{prefix}.id duplicates an earlier runner track")
        else:
            seen_ids.add(track_id)
        if not _non_empty_string(track.get("status")):
            errors.append(f"{prefix}.status must be a non-empty string")
        if example:
            if not _non_empty_string(track.get("hardware_fingerprint_sha256")):
                errors.append(f"{prefix}.hardware_fingerprint_sha256 must be a non-empty string")
        elif not _looks_sha256(track.get("hardware_fingerprint_sha256")):
            errors.append(f"{prefix}.hardware_fingerprint_sha256 must be a sha256 hex string")
        if track.get("disclosed_to_candidates") is not False:
            errors.append(f"{prefix}.disclosed_to_candidates must be false")
    expected = {
        track.get("id")
        for track in replay_contract.get("runner_tracks", [])
        if isinstance(track, dict) and _non_empty_string(track.get("id"))
    }
    if seen_ids != expected:
        errors.append("runner_tracks must match replay contract runner_tracks")
    return errors


def validate_hidden_manifest(manifest: dict[str, Any], replay_contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing(manifest, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("hidden manifest missing fields: " + ", ".join(missing))
        return errors
    example = _is_example(manifest)
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("challenge") != CHALLENGE or manifest.get("challenge") != replay_contract.get("challenge"):
        errors.append(f"challenge must be {CHALLENGE}")
    if manifest.get("manifest_kind") != MANIFEST_KIND:
        errors.append(f"manifest_kind must be {MANIFEST_KIND}")
    if manifest.get("hash_algorithm") != HASH_ALGORITHM:
        errors.append(f"hash_algorithm must be {HASH_ALGORITHM}")
    if not isinstance(manifest.get("hidden_manifest_ready"), bool):
        errors.append("hidden_manifest_ready must be boolean")
    if example:
        disclaimer = str(manifest.get("disclaimer", "")).lower()
        if "not a real hidden manifest" not in disclaimer:
            errors.append("schema-only hidden manifest must say it is not a real hidden manifest")
        if manifest.get("hidden_manifest_ready") is not False:
            errors.append("schema-only hidden manifest must not be ready")

    errors.extend(_validate_case_policy(manifest.get("case_policy")))
    errors.extend(_validate_case_suites(manifest.get("case_suites"), example))
    errors.extend(_validate_runner_tracks(manifest.get("runner_tracks"), replay_contract, example))
    errors.extend(_validate_hash_field(manifest, "tolerance_matrix_hash", example))
    errors.extend(_validate_hash_field(manifest, "timing_policy_hash", example))
    return errors
