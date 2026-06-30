from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VALID_RUNNER_STATUSES = {"example", "pending-freeze", "frozen"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "source",
    "runner_id",
    "runner_status",
    "clean_checkout_required",
    "network_disabled",
    "dependency_lock",
    "fixed_runner_tracks",
    "hidden_case_manifest",
    "timing_policy",
    "replay_outputs",
    "anti_cheat",
}
REQUIRED_DEPENDENCY_LOCK = {"kind", "digest", "python", "packages"}
REQUIRED_TRACK_FIELDS = {
    "id",
    "status",
    "backend",
    "hardware_fingerprint_required",
    "memory_cap",
}
REQUIRED_HIDDEN_MANIFEST = {"path", "hash_algorithm", "hidden_cases_bundled", "case_suites"}
REQUIRED_REPLAY_OUTPUTS = {
    "replay_result_json",
    "result_card_markdown",
    "runner_log",
    "timing_log",
    "case_suite_hash",
    "code_hash",
}
REQUIRED_ANTI_CHEAT = {
    "correctness_first",
    "candidate_selection_uses_hidden_cases",
    "hidden_shapes_disclosed_before_candidate_freeze",
    "network_disabled_during_scoring",
    "forbidden_paths_checked",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _missing_fields(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _require_object(payload: dict[str, Any], field: str, errors: list[str]) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, dict):
        errors.append(f"{field} must be an object")
        return {}
    return value


def _require_list(payload: dict[str, Any], field: str, errors: list[str]) -> list[Any]:
    value = payload.get(field)
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _runner_track_ids(contract: dict[str, Any]) -> set[str]:
    return {track["id"] for track in contract.get("runner_tracks", []) if isinstance(track, dict)}


def validate_manifest(manifest: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing_fields(manifest, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("runner manifest missing fields: " + ", ".join(missing))
        return errors

    if manifest.get("challenge") != contract.get("challenge"):
        errors.append("runner manifest challenge does not match verifier contract")
    if manifest.get("source") == "example-schema-only":
        disclaimer = str(manifest.get("disclaimer", "")).lower()
        if "not an official runner" not in disclaimer:
            errors.append("example runner manifest disclaimer must say it is not an official runner")
    if manifest.get("runner_status") not in VALID_RUNNER_STATUSES:
        errors.append("runner_status must be example, pending-freeze, or frozen")
    if manifest.get("clean_checkout_required") is not True:
        errors.append("clean_checkout_required must be true")
    if manifest.get("network_disabled") is not True:
        errors.append("network_disabled must be true")

    dependency_lock = _require_object(manifest, "dependency_lock", errors)
    missing_dependency = _missing_fields(dependency_lock, REQUIRED_DEPENDENCY_LOCK)
    if missing_dependency:
        errors.append("dependency_lock missing fields: " + ", ".join(missing_dependency))
    for field in ["kind", "digest", "python"]:
        if field in dependency_lock and not _non_empty_string(dependency_lock[field]):
            errors.append(f"dependency_lock.{field} must be a non-empty string")
    if "packages" in dependency_lock and not isinstance(dependency_lock["packages"], list):
        errors.append("dependency_lock.packages must be a list")

    known_tracks = _runner_track_ids(contract)
    tracks = _require_list(manifest, "fixed_runner_tracks", errors)
    if not tracks:
        errors.append("fixed_runner_tracks must not be empty")
    for index, track in enumerate(tracks):
        if not isinstance(track, dict):
            errors.append(f"fixed_runner_tracks[{index}] must be an object")
            continue
        missing_track = _missing_fields(track, REQUIRED_TRACK_FIELDS)
        if missing_track:
            errors.append(f"fixed_runner_tracks[{index}] missing fields: " + ", ".join(missing_track))
        if track.get("id") not in known_tracks:
            errors.append(f"fixed_runner_tracks[{index}].id must be a known fixed runner track")
        if track.get("status") not in VALID_RUNNER_STATUSES:
            errors.append(f"fixed_runner_tracks[{index}].status must be example, pending-freeze, or frozen")
        if track.get("hardware_fingerprint_required") is not True:
            errors.append(f"fixed_runner_tracks[{index}].hardware_fingerprint_required must be true")
        if not _non_empty_string(track.get("memory_cap")):
            errors.append(f"fixed_runner_tracks[{index}].memory_cap must be a non-empty string")

    hidden_manifest = _require_object(manifest, "hidden_case_manifest", errors)
    missing_hidden = _missing_fields(hidden_manifest, REQUIRED_HIDDEN_MANIFEST)
    if missing_hidden:
        errors.append("hidden_case_manifest missing fields: " + ", ".join(missing_hidden))
    expected_hidden_policy = contract.get("hidden_case_policy", {})
    if hidden_manifest.get("path") != expected_hidden_policy.get("manifest_path_on_trusted_runners"):
        errors.append("hidden_case_manifest.path must match verifier contract")
    if hidden_manifest.get("hash_algorithm") != expected_hidden_policy.get("hash_algorithm"):
        errors.append("hidden_case_manifest.hash_algorithm must match verifier contract")
    if hidden_manifest.get("hidden_cases_bundled") is not False:
        errors.append("hidden_case_manifest.hidden_cases_bundled must be false")
    case_suites = _require_list(hidden_manifest, "case_suites", errors)
    if not case_suites:
        errors.append("hidden_case_manifest.case_suites must not be empty")
    for index, suite in enumerate(case_suites):
        if not isinstance(suite, dict):
            errors.append(f"hidden_case_manifest.case_suites[{index}] must be an object")
            continue
        for field in ["id", "purpose", "hash"]:
            if not _non_empty_string(suite.get(field)):
                errors.append(f"hidden_case_manifest.case_suites[{index}].{field} must be a non-empty string")

    timing_policy = _require_object(manifest, "timing_policy", errors)
    contract_timing = contract.get("timing_policy", {})
    for field in ["aggregation", "timer", "memory_cap"]:
        if timing_policy.get(field) != contract_timing.get(field):
            errors.append(f"timing_policy.{field} must match verifier contract")
    if timing_policy.get("hardware_fingerprint_required") is not True:
        errors.append("timing_policy.hardware_fingerprint_required must be true")

    replay_outputs = _require_object(manifest, "replay_outputs", errors)
    missing_outputs = _missing_fields(replay_outputs, REQUIRED_REPLAY_OUTPUTS)
    if missing_outputs:
        errors.append("replay_outputs missing fields: " + ", ".join(missing_outputs))

    anti_cheat = _require_object(manifest, "anti_cheat", errors)
    missing_anti_cheat = _missing_fields(anti_cheat, REQUIRED_ANTI_CHEAT)
    if missing_anti_cheat:
        errors.append("anti_cheat missing fields: " + ", ".join(missing_anti_cheat))
    if anti_cheat.get("correctness_first") is not True:
        errors.append("anti_cheat.correctness_first must be true")
    if anti_cheat.get("candidate_selection_uses_hidden_cases") is not False:
        errors.append("anti_cheat.candidate_selection_uses_hidden_cases must be false")
    if anti_cheat.get("hidden_shapes_disclosed_before_candidate_freeze") is not False:
        errors.append("anti_cheat.hidden_shapes_disclosed_before_candidate_freeze must be false")
    if anti_cheat.get("network_disabled_during_scoring") is not True:
        errors.append("anti_cheat.network_disabled_during_scoring must be true")
    if anti_cheat.get("forbidden_paths_checked") is not True:
        errors.append("anti_cheat.forbidden_paths_checked must be true")

    return errors
