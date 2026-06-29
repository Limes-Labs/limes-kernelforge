from __future__ import annotations

import json
from pathlib import Path
from typing import Any


HIDDEN_METRIC = "hidden_geomean_runtime_ms"
PUBLIC_SCORE_FIELDS = {
    "hidden_geomean_runtime_ms",
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_speedup_vs_reference",
}
PUBLIC_METRIC_FIELDS = {
    "correct",
    "max_abs_error",
    "max_rel_error",
    "public_runtime_delta_ms",
    "backend",
    "tolerance",
}
REPLAY_FIELDS = {"trusted_runner", "fixed_runner_track", "integration_audit"}
BASE_ENTRY_FIELDS = {
    "challenge",
    "submission_id",
    "status",
    "track",
    "commit",
    "score",
    "metrics",
    "replay",
    "links",
}
PRE_VERIFIED_STATUSES = {"local", "candidate"}
POST_VERIFIED_STATUSES = {"verified", "promoted", "replicated", "scaled"}
PROMOTED_OR_LATER = {"promoted", "replicated", "scaled"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _missing_fields(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _runner_track_ids(contract: dict[str, Any]) -> set[str]:
    return {track["id"] for track in contract.get("runner_tracks", []) if isinstance(track, dict)}


def _validate_entry(entry: dict[str, Any], contract: dict[str, Any], index: int) -> list[str]:
    prefix = f"entries[{index}]"
    errors: list[str] = []
    missing = _missing_fields(entry, BASE_ENTRY_FIELDS)
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        return errors

    if entry["challenge"] != contract.get("challenge"):
        errors.append(f"{prefix}.challenge does not match verifier contract")

    status = entry.get("status")
    if status not in contract.get("status_model", []):
        errors.append(f"{prefix}.status is not in the verifier status model")

    score = entry.get("score")
    metrics = entry.get("metrics")
    replay = entry.get("replay")
    links = entry.get("links")
    if not isinstance(score, dict):
        errors.append(f"{prefix}.score must be an object")
        score = {}
    if not isinstance(metrics, dict):
        errors.append(f"{prefix}.metrics must be an object")
        metrics = {}
    if not isinstance(replay, dict):
        errors.append(f"{prefix}.replay must be an object")
        replay = {}
    if not isinstance(links, dict):
        errors.append(f"{prefix}.links must be an object")
        links = {}

    for field_group, payload, required in [
        ("score", score, PUBLIC_SCORE_FIELDS),
        ("metrics", metrics, PUBLIC_METRIC_FIELDS),
        ("replay", replay, REPLAY_FIELDS),
    ]:
        missing = _missing_fields(payload, required)
        if missing:
            errors.append(f"{prefix}.{field_group} missing fields: {', '.join(missing)}")

    hidden_value = score.get(HIDDEN_METRIC)
    fixed_track = replay.get("fixed_runner_track")
    runner_track_ids = _runner_track_ids(contract)
    if status in PRE_VERIFIED_STATUSES and hidden_value is not None:
        errors.append(f"{prefix}.{HIDDEN_METRIC} must be null before verified status")
    if status in POST_VERIFIED_STATUSES and not _is_number(hidden_value):
        errors.append(f"{prefix}.{HIDDEN_METRIC} must be numeric for verified or later status")
    if status in POST_VERIFIED_STATUSES and not replay.get("trusted_runner"):
        errors.append(f"{prefix}.replay.trusted_runner is required for verified or later status")
    if status in POST_VERIFIED_STATUSES and fixed_track not in runner_track_ids:
        errors.append(f"{prefix}.replay.fixed_runner_track must be a known fixed runner track")
    if status in PROMOTED_OR_LATER and not links.get("result_card"):
        errors.append(f"{prefix}.links.result_card is required for promoted or later status")
    if status in PROMOTED_OR_LATER and metrics.get("correct") is not True:
        errors.append(f"{prefix}.metrics.correct must remain true for promoted or later status")
    if status == "scaled" and replay.get("integration_audit") is not True:
        errors.append(f"{prefix}.replay.integration_audit must be true for scaled status")
    return errors


def validate_payload(payload: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("challenge") != contract.get("challenge"):
        errors.append("payload challenge does not match verifier contract")
    if payload.get("source") == "example-fixture":
        disclaimer = str(payload.get("disclaimer", "")).lower()
        if "not an official leaderboard" not in disclaimer:
            errors.append("example fixture disclaimer must say it is not an official leaderboard")
    entries = payload.get("entries")
    if not isinstance(entries, list) or not entries:
        return errors + ["payload entries must be a non-empty list"]
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{index}] must be an object")
            continue
        errors.extend(_validate_entry(entry, contract, index))
    return errors
