from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPLAY_STATUSES = {"verified", "promoted", "replicated", "scaled"}
PROMOTED_OR_LATER = {"promoted", "replicated", "scaled"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "source",
    "submission_id",
    "status",
    "commit",
    "score",
    "metrics",
    "replay",
    "promotion",
    "links",
}
REQUIRED_METRICS = {
    "hidden_geomean_runtime_ms",
    "reference_hidden_geomean_runtime_ms",
    "hidden_speedup_vs_reference",
    "max_abs_error",
    "max_rel_error",
    "peak_memory_mb",
    "runner_track",
    "case_suite_hash",
    "code_hash",
    "integration_audit",
}
REQUIRED_REPLAY_FIELDS = {
    "trusted_runner",
    "run_id",
    "clean_checkout",
    "network_disabled",
    "fixed_runner_track",
    "code_hash",
    "case_suite_hash",
    "verifier_contract_hash",
    "dependency_lock",
}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _missing_fields(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _runner_track_ids(contract: dict[str, Any]) -> set[str]:
    return {track["id"] for track in contract.get("runner_tracks", []) if isinstance(track, dict)}


def validate_result(payload: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing_fields(payload, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("result missing fields: " + ", ".join(missing))
        return errors

    if payload.get("challenge") != contract.get("challenge"):
        errors.append("result challenge does not match verifier contract")
    if payload.get("source") == "example-schema-only":
        disclaimer = str(payload.get("disclaimer", "")).lower()
        if "not an official result" not in disclaimer:
            errors.append("example replay result disclaimer must say it is not an official result")

    status = payload.get("status")
    if status not in REPLAY_STATUSES:
        errors.append("replay result status must be verified, promoted, replicated, or scaled")
    if status not in contract.get("status_model", []):
        errors.append("replay result status is not in verifier status model")

    score = payload.get("score")
    metrics = payload.get("metrics")
    replay = payload.get("replay")
    promotion = payload.get("promotion")
    links = payload.get("links")
    if not _is_number(score):
        errors.append("score must be numeric")
    if not isinstance(metrics, dict):
        errors.append("metrics must be an object")
        metrics = {}
    if not isinstance(replay, dict):
        errors.append("replay must be an object")
        replay = {}
    if not isinstance(promotion, dict):
        errors.append("promotion must be an object")
        promotion = {}
    if not isinstance(links, dict):
        errors.append("links must be an object")
        links = {}

    missing_metrics = _missing_fields(metrics, REQUIRED_METRICS)
    if missing_metrics:
        errors.append("metrics missing fields: " + ", ".join(missing_metrics))
    for field in [
        "hidden_geomean_runtime_ms",
        "reference_hidden_geomean_runtime_ms",
        "hidden_speedup_vs_reference",
        "max_abs_error",
        "max_rel_error",
    ]:
        if field in metrics and not _is_number(metrics[field]):
            errors.append(f"metrics.{field} must be numeric")
    if "hidden_geomean_runtime_ms" in metrics and _is_number(score) and metrics["hidden_geomean_runtime_ms"] != score:
        errors.append("score must equal metrics.hidden_geomean_runtime_ms")

    runner_track_ids = _runner_track_ids(contract)
    if metrics.get("runner_track") not in runner_track_ids:
        errors.append("metrics.runner_track must be a known fixed runner track")

    missing_replay = _missing_fields(replay, REQUIRED_REPLAY_FIELDS)
    if missing_replay:
        errors.append("replay missing fields: " + ", ".join(missing_replay))
    for field in [
        "trusted_runner",
        "run_id",
        "fixed_runner_track",
        "code_hash",
        "case_suite_hash",
        "verifier_contract_hash",
        "dependency_lock",
    ]:
        if field in replay and not _non_empty_string(replay[field]):
            errors.append(f"replay.{field} must be a non-empty string")
    if replay.get("fixed_runner_track") != metrics.get("runner_track"):
        errors.append("replay.fixed_runner_track must match metrics.runner_track")
    if replay.get("code_hash") != metrics.get("code_hash"):
        errors.append("replay.code_hash must match metrics.code_hash")
    if replay.get("case_suite_hash") != metrics.get("case_suite_hash"):
        errors.append("replay.case_suite_hash must match metrics.case_suite_hash")
    if replay.get("clean_checkout") is not True:
        errors.append("replay.clean_checkout must be true")
    if replay.get("network_disabled") is not True:
        errors.append("replay.network_disabled must be true")

    gates_passed = promotion.get("gates_passed")
    gates_failed = promotion.get("gates_failed")
    if not isinstance(gates_passed, list):
        errors.append("promotion.gates_passed must be a list")
    if not isinstance(gates_failed, list):
        errors.append("promotion.gates_failed must be a list")
    if status in PROMOTED_OR_LATER and promotion.get("promotable") is not True:
        errors.append("promotion.promotable must be true for promoted or later status")
    if status in PROMOTED_OR_LATER and not links.get("result_card"):
        errors.append("links.result_card is required for promoted or later status")
    if status == "scaled" and promotion.get("integration_audit") is not True:
        errors.append("promotion.integration_audit must be true for scaled status")
    if status == "scaled" and metrics.get("integration_audit") is not True:
        errors.append("metrics.integration_audit must be true for scaled status")
    return errors
