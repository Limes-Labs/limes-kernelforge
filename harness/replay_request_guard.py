from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from harness.candidate_packet_guard import validate_packet as validate_candidate_packet
from harness.submission_guard import load_json


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1.0"
CHALLENGE = "limes-kernelforge"
REQUEST_KIND = "trusted-replay-request"
REQUESTED_STATUS = "verified"
ALLOWED_OUTPUTS = {
    "status",
    "official_result_packet",
    "promotion_gate_summary",
    "fixed_runner_summary",
    "result_card_if_promotable",
}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "request_kind",
    "source",
    "request_id",
    "submission_id",
    "candidate_packet_id",
    "candidate_commit",
    "requested_status",
    "requested_metric",
    "direction",
    "runner_track",
    "replay_ready",
    "artifacts",
    "eligibility",
    "anti_probing",
    "replay_budget",
    "review",
}
REQUIRED_ARTIFACTS = {
    "candidate_packet",
    "submission_manifest",
    "source_bundle",
    "search_ledger",
    "agent_notes",
    "public_score",
    "invariant_probes",
    "public_audit",
}
REQUIRED_ARTIFACT_FIELDS = {"path", "sha256", "validated"}
REQUIRED_ELIGIBILITY = {
    "candidate_packet_validated",
    "submission_preflight_passed",
    "source_bundle_validated",
    "search_ledger_validated",
    "agent_notes_validated",
    "public_score_present",
    "public_correctness_passed",
    "public_stress_correctness_passed",
    "invariant_probes_passed",
    "public_audit_passed",
    "local_bundle_validated",
    "no_forbidden_paths",
    "fixed_runner_track_declared",
    "candidate_frozen",
    "mutable_after_request",
}
REQUIRED_ANTI_PROBING = {
    "hidden_feedback_requested",
    "hidden_metric_seen_by_submitter",
    "selected_after_hidden_feedback",
    "private_leaderboard_feedback_used",
    "fixed_runner_feedback_before_candidate_freeze",
    "request_influences_candidate_selection",
    "same_candidate_previously_replayed",
    "requested_outputs",
}
REQUIRED_REPLAY_BUDGET = {
    "max_trusted_replays_per_submission",
    "max_trusted_replays_per_team_per_7_days",
    "max_trusted_replays_per_team_per_30_days",
    "request_count_for_submission",
    "team_request_count_7_days",
    "team_request_count_30_days",
}
REQUIRED_REVIEW = {"reviewer", "decision", "notes"}


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_path(path_text: str, root: Path = ROOT) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return root / path


def _is_example(request: dict[str, Any]) -> bool:
    return request.get("source") == "example-schema-only"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _looks_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value.lower()
    )


def _missing(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _runner_track_ids(contract: dict[str, Any]) -> set[str]:
    return {
        track["id"]
        for track in contract.get("runner_tracks", [])
        if isinstance(track, dict) and _non_empty_string(track.get("id"))
    }


def _artifact_errors(artifacts: Any, root: Path, verify_files: bool, example: bool) -> list[str]:
    if not isinstance(artifacts, dict):
        return ["artifacts must be an object"]
    errors: list[str] = []
    missing = _missing(artifacts, REQUIRED_ARTIFACTS)
    if missing:
        errors.append("artifacts missing fields: " + ", ".join(missing))
    for name in sorted(REQUIRED_ARTIFACTS.intersection(artifacts)):
        artifact = artifacts.get(name)
        if not isinstance(artifact, dict):
            errors.append(f"artifacts.{name} must be an object")
            continue
        missing_fields = _missing(artifact, REQUIRED_ARTIFACT_FIELDS)
        if missing_fields:
            errors.append(f"artifacts.{name} missing fields: " + ", ".join(missing_fields))
        if not _non_empty_string(artifact.get("path")):
            errors.append(f"artifacts.{name}.path must be a non-empty string")
        if example:
            if not _non_empty_string(artifact.get("sha256")):
                errors.append(f"artifacts.{name}.sha256 must be a non-empty string")
        elif not _looks_sha256(artifact.get("sha256")):
            errors.append(f"artifacts.{name}.sha256 must be a sha256 hex string")
        if not isinstance(artifact.get("validated"), bool):
            errors.append(f"artifacts.{name}.validated must be boolean")
        if verify_files and not example and _non_empty_string(artifact.get("path")):
            path = resolve_path(artifact["path"], root)
            if not path.exists():
                errors.append(f"artifacts.{name}.path does not exist: {artifact['path']}")
            elif sha256_file(path) != artifact.get("sha256"):
                errors.append(f"artifacts.{name}.sha256 does not match file contents")
    return errors


def _validate_eligibility(eligibility: Any, replay_ready: bool) -> list[str]:
    if not isinstance(eligibility, dict):
        return ["eligibility must be an object"]
    errors: list[str] = []
    missing = _missing(eligibility, REQUIRED_ELIGIBILITY)
    if missing:
        errors.append("eligibility missing fields: " + ", ".join(missing))
        return errors
    true_fields = REQUIRED_ELIGIBILITY - {"mutable_after_request"}
    for field in sorted(true_fields):
        if not isinstance(eligibility.get(field), bool):
            errors.append(f"eligibility.{field} must be boolean")
        elif replay_ready and eligibility[field] is not True:
            errors.append(f"eligibility.{field} must be true when replay_ready is true")
    if not isinstance(eligibility.get("mutable_after_request"), bool):
        errors.append("eligibility.mutable_after_request must be boolean")
    elif eligibility["mutable_after_request"] is not False:
        errors.append("eligibility.mutable_after_request must be false")
    return errors


def _validate_anti_probing(anti_probing: Any) -> list[str]:
    if not isinstance(anti_probing, dict):
        return ["anti_probing must be an object"]
    errors: list[str] = []
    missing = _missing(anti_probing, REQUIRED_ANTI_PROBING)
    if missing:
        errors.append("anti_probing missing fields: " + ", ".join(missing))
        return errors
    for field in sorted(REQUIRED_ANTI_PROBING - {"requested_outputs"}):
        if anti_probing.get(field) is not False:
            errors.append(f"anti_probing.{field} must be false")
    outputs = anti_probing.get("requested_outputs")
    if not isinstance(outputs, list) or not outputs:
        errors.append("anti_probing.requested_outputs must be a non-empty list")
    else:
        unknown = sorted(output for output in outputs if output not in ALLOWED_OUTPUTS)
        if unknown:
            errors.append("anti_probing.requested_outputs contains unsupported outputs: " + ", ".join(unknown))
    return errors


def _validate_replay_budget(budget: Any, contract: dict[str, Any]) -> list[str]:
    if not isinstance(budget, dict):
        return ["replay_budget must be an object"]
    errors: list[str] = []
    missing = _missing(budget, REQUIRED_REPLAY_BUDGET)
    if missing:
        errors.append("replay_budget missing fields: " + ", ".join(missing))
        return errors
    policy = contract.get("trusted_replay_request_policy", {})
    expected = {
        "max_trusted_replays_per_submission": policy.get("max_trusted_replays_per_submission", 1),
        "max_trusted_replays_per_team_per_7_days": policy.get("max_trusted_replays_per_team_per_7_days", 2),
        "max_trusted_replays_per_team_per_30_days": policy.get("max_trusted_replays_per_team_per_30_days", 5),
    }
    for field, expected_value in expected.items():
        if budget.get(field) != expected_value:
            errors.append(f"replay_budget.{field} must match verifier contract")
    count_limits = {
        "request_count_for_submission": "max_trusted_replays_per_submission",
        "team_request_count_7_days": "max_trusted_replays_per_team_per_7_days",
        "team_request_count_30_days": "max_trusted_replays_per_team_per_30_days",
    }
    for count_field, max_field in count_limits.items():
        value = budget.get(count_field)
        limit = budget.get(max_field)
        if not isinstance(value, int) or value < 0:
            errors.append(f"replay_budget.{count_field} must be a non-negative integer")
        elif isinstance(limit, int) and value > limit:
            errors.append(f"replay_budget.{count_field} must not exceed {max_field}")
    if budget.get("request_count_for_submission") != 1:
        errors.append("replay_budget.request_count_for_submission must be 1")
    return errors


def _validate_review(review: Any, replay_ready: bool, example: bool) -> list[str]:
    if not isinstance(review, dict):
        return ["review must be an object"]
    errors: list[str] = []
    missing = _missing(review, REQUIRED_REVIEW)
    if missing:
        errors.append("review missing fields: " + ", ".join(missing))
        return errors
    if not _non_empty_string(review.get("reviewer")):
        errors.append("review.reviewer must be a non-empty string")
    if review.get("decision") not in {"example", "reject", "hold", "approve"}:
        errors.append("review.decision must be example, reject, hold, or approve")
    if replay_ready and review.get("decision") != "approve":
        errors.append("review.decision must be approve when replay_ready is true")
    if not example and review.get("decision") == "example":
        errors.append("review.decision must not be example for real replay requests")
    if not _non_empty_string(review.get("notes")):
        errors.append("review.notes must be a non-empty string")
    return errors


def _validate_real_candidate_packet(
    request: dict[str, Any],
    challenge_contract: dict[str, Any],
    root: Path,
) -> list[str]:
    artifacts = request.get("artifacts", {})
    if not isinstance(artifacts, dict) or not isinstance(artifacts.get("candidate_packet"), dict):
        return []
    candidate_packet_path = resolve_path(artifacts["candidate_packet"].get("path", ""), root)
    if not candidate_packet_path.exists():
        return []
    packet = load_json(candidate_packet_path)
    errors = [
        f"candidate_packet: {error}"
        for error in validate_candidate_packet(packet, challenge_contract, root=root, verify_files=True)
    ]
    if packet.get("packet_id") != request.get("candidate_packet_id"):
        errors.append("candidate_packet_id must match candidate packet packet_id")
    if packet.get("commit") != request.get("candidate_commit"):
        errors.append("candidate_commit must match candidate packet commit")
    if request.get("replay_ready") is True and packet.get("candidate_ready") is not True:
        errors.append("candidate packet candidate_ready must be true when replay_ready is true")
    return errors


def validate_request(
    request: dict[str, Any],
    contract: dict[str, Any],
    root: Path = ROOT,
    verify_files: bool = True,
    challenge_contract: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    missing = _missing(request, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("replay request missing fields: " + ", ".join(missing))
        return errors

    example = _is_example(request)
    replay_ready = request.get("replay_ready") is True
    if request.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if request.get("challenge") != CHALLENGE or request.get("challenge") != contract.get("challenge"):
        errors.append(f"challenge must be {CHALLENGE}")
    if request.get("request_kind") != REQUEST_KIND:
        errors.append(f"request_kind must be {REQUEST_KIND}")
    if example:
        disclaimer = str(request.get("disclaimer", "")).lower()
        if "not an official replay request" not in disclaimer:
            errors.append("schema-only replay request must say it is not an official replay request")
        if replay_ready:
            errors.append("schema-only replay request must not be replay_ready")
    if not isinstance(request.get("replay_ready"), bool):
        errors.append("replay_ready must be boolean")
    if request.get("requested_status") != REQUESTED_STATUS:
        errors.append(f"requested_status must be {REQUESTED_STATUS}")
    if request.get("requested_metric") != contract.get("official_primary_metric"):
        errors.append("requested_metric must match verifier contract official_primary_metric")
    if request.get("direction") != contract.get("score_direction"):
        errors.append("direction must match verifier contract score_direction")
    for field in ["request_id", "submission_id", "candidate_packet_id", "candidate_commit"]:
        if not _non_empty_string(request.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if request.get("runner_track") not in _runner_track_ids(contract):
        errors.append("runner_track must be a known fixed runner track")

    errors.extend(_artifact_errors(request.get("artifacts"), root, verify_files, example))
    errors.extend(_validate_eligibility(request.get("eligibility"), replay_ready))
    errors.extend(_validate_anti_probing(request.get("anti_probing")))
    errors.extend(_validate_replay_budget(request.get("replay_budget"), contract))
    errors.extend(_validate_review(request.get("review"), replay_ready, example))
    if verify_files and not example:
        errors.extend(_validate_real_candidate_packet(request, challenge_contract or contract, root))
    return errors
