from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROMOTION_STATUSES = {"verified", "promoted", "replicated", "scaled"}
PROMOTED_OR_LATER = {"promoted", "replicated", "scaled"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "source",
    "packet_id",
    "requested_status",
    "submission_id",
    "submission_commit",
    "promotion_ready",
    "official_metric",
    "direction",
    "score",
    "baseline_score",
    "runner_track",
    "artifacts",
    "evidence",
    "gates",
    "review",
}
REQUIRED_ARTIFACTS = {
    "submission_manifest",
    "agent_notes",
    "runner_manifest",
    "baseline_record",
    "replay_result",
    "result_card",
    "leaderboard_entry",
}
REQUIRED_ARTIFACT_FIELDS = {"path", "sha256", "validated"}
REQUIRED_EVIDENCE = {
    "submission_preflight_passed",
    "agent_notes_validated",
    "runner_manifest_validated",
    "baseline_record_validated",
    "replay_result_validated",
    "leaderboard_entry_validated",
    "clean_checkout",
    "network_disabled",
    "no_forbidden_paths",
    "hidden_shapes_not_disclosed",
    "public_timings_candidate_only",
    "correctness_passed",
    "numerical_tolerance_passed",
    "fixed_runner_track_present",
    "memory_cap_respected",
    "invalid_optimization_audit",
    "result_card_present",
    "integration_audit",
    "scaled_audit",
}
REQUIRED_GATES = {"passed", "failed", "blocked"}
REQUIRED_REVIEW = {"reviewer", "decision", "notes"}


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


def _validate_artifacts(artifacts: dict[str, Any], errors: list[str]) -> None:
    missing_artifacts = _missing_fields(artifacts, REQUIRED_ARTIFACTS)
    if missing_artifacts:
        errors.append("artifacts missing fields: " + ", ".join(missing_artifacts))
    for name in sorted(REQUIRED_ARTIFACTS.intersection(artifacts)):
        artifact = artifacts.get(name)
        if not isinstance(artifact, dict):
            errors.append(f"artifacts.{name} must be an object")
            continue
        missing_fields = _missing_fields(artifact, REQUIRED_ARTIFACT_FIELDS)
        if missing_fields:
            errors.append(f"artifacts.{name} missing fields: " + ", ".join(missing_fields))
        for field in ["path", "sha256"]:
            if field in artifact and not _non_empty_string(artifact[field]):
                errors.append(f"artifacts.{name}.{field} must be a non-empty string")
        if artifact.get("validated") is not True:
            errors.append(f"artifacts.{name}.validated must be true")


def validate_packet(packet: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing_fields(packet, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("promotion packet missing fields: " + ", ".join(missing))
        return errors

    if packet.get("challenge") != contract.get("challenge"):
        errors.append("promotion packet challenge does not match verifier contract")
    if packet.get("source") == "example-schema-only":
        disclaimer = str(packet.get("disclaimer", "")).lower()
        if "not an official promotion" not in disclaimer:
            errors.append("example promotion packet disclaimer must say it is not an official promotion")

    requested_status = packet.get("requested_status")
    if requested_status not in PROMOTION_STATUSES:
        errors.append("requested_status must be verified, promoted, replicated, or scaled")
    if requested_status not in contract.get("status_model", []):
        errors.append("requested_status is not in verifier status model")
    if packet.get("official_metric") != contract.get("official_primary_metric"):
        errors.append("official_metric must match verifier contract official_primary_metric")
    if packet.get("direction") != contract.get("score_direction"):
        errors.append("direction must match verifier contract score_direction")
    if packet.get("runner_track") not in _runner_track_ids(contract):
        errors.append("runner_track must be a known fixed runner track")
    if not _is_number(packet.get("score")):
        errors.append("score must be numeric")
    if not _is_number(packet.get("baseline_score")):
        errors.append("baseline_score must be numeric")
    if not _non_empty_string(packet.get("packet_id")):
        errors.append("packet_id must be a non-empty string")
    if not _non_empty_string(packet.get("submission_id")):
        errors.append("submission_id must be a non-empty string")
    if not _non_empty_string(packet.get("submission_commit")):
        errors.append("submission_commit must be a non-empty string")

    artifacts = _require_object(packet, "artifacts", errors)
    _validate_artifacts(artifacts, errors)

    evidence = _require_object(packet, "evidence", errors)
    missing_evidence = _missing_fields(evidence, REQUIRED_EVIDENCE)
    if missing_evidence:
        errors.append("evidence missing fields: " + ", ".join(missing_evidence))
    for field in [
        "submission_preflight_passed",
        "agent_notes_validated",
        "runner_manifest_validated",
        "baseline_record_validated",
        "replay_result_validated",
        "leaderboard_entry_validated",
        "clean_checkout",
        "network_disabled",
        "no_forbidden_paths",
        "hidden_shapes_not_disclosed",
        "public_timings_candidate_only",
        "correctness_passed",
        "numerical_tolerance_passed",
        "fixed_runner_track_present",
    ]:
        if field in evidence and evidence.get(field) is not True:
            errors.append(f"evidence.{field} must be true")
    if requested_status in PROMOTED_OR_LATER and evidence.get("result_card_present") is not True:
        errors.append("evidence.result_card_present must be true for promoted or later status")
    if requested_status in PROMOTED_OR_LATER and evidence.get("memory_cap_respected") is not True:
        errors.append("evidence.memory_cap_respected must be true for promoted or later status")
    if requested_status in PROMOTED_OR_LATER and evidence.get("invalid_optimization_audit") is not True:
        errors.append("evidence.invalid_optimization_audit must be true for promoted or later status")
    if requested_status == "scaled" and evidence.get("integration_audit") is not True:
        errors.append("evidence.integration_audit must be true for scaled status")
    if requested_status == "scaled" and evidence.get("scaled_audit") is not True:
        errors.append("evidence.scaled_audit must be true for scaled status")

    gates = _require_object(packet, "gates", errors)
    missing_gates = _missing_fields(gates, REQUIRED_GATES)
    if missing_gates:
        errors.append("gates missing fields: " + ", ".join(missing_gates))
    passed = _require_list(gates, "passed", errors)
    failed = _require_list(gates, "failed", errors)
    blocked = _require_list(gates, "blocked", errors)
    if requested_status in PROMOTED_OR_LATER and (failed or blocked):
        errors.append("promoted or later packets must not have failed or blocked gates")
    if requested_status in PROMOTED_OR_LATER and not passed:
        errors.append("promoted or later packets must list passed gates")

    review = _require_object(packet, "review", errors)
    missing_review = _missing_fields(review, REQUIRED_REVIEW)
    if missing_review:
        errors.append("review missing fields: " + ", ".join(missing_review))
    if not _non_empty_string(review.get("reviewer")):
        errors.append("review.reviewer must be a non-empty string")
    if review.get("decision") not in {"example", "reject", "hold", "approve"}:
        errors.append("review.decision must be example, reject, hold, or approve")
    if requested_status in PROMOTED_OR_LATER and review.get("decision") != "approve":
        errors.append("review.decision must be approve for promoted or later status")
    if requested_status in PROMOTED_OR_LATER and packet.get("promotion_ready") is not True:
        errors.append("promotion_ready must be true for promoted or later status")
    if packet.get("source") == "example-schema-only" and packet.get("promotion_ready") is True:
        errors.append("schema-only example promotion packet must not be promotion_ready")

    return errors
