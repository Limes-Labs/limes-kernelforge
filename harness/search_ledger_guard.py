from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "submission_id",
    "ledger_id",
    "source",
    "search_budget",
    "candidate_selection",
    "attempts",
    "negative_or_mixed_findings",
    "public_data_boundary",
    "replay_request",
}
REQUIRED_BUDGET = {
    "agent_runs",
    "wall_clock_minutes",
    "local_hardware",
    "max_attempts_planned",
    "actual_attempts",
    "network_used",
    "native_extension_used",
    "fixed_runner_feedback_used",
}
REQUIRED_SELECTION = {
    "selected_attempt_id",
    "selection_metric",
    "direction",
    "baseline_score",
    "selected_score",
    "selection_reason",
    "stopped_reason",
    "selected_after_seeing_hidden_cases",
}
REQUIRED_ATTEMPT = {
    "id",
    "status",
    "primitive",
    "hypothesis",
    "changed_files",
    "command",
    "correct",
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_stress_correct",
    "invariant_probes_passed",
    "backend",
    "result_summary",
    "failure_modes",
}
REQUIRED_BOUNDARY = {
    "used_hidden_cases",
    "used_private_runner_feedback",
    "public_timings_candidate_only",
}
REQUIRED_REPLAY = {"requested", "runner_track", "rationale"}
ALLOWED_ATTEMPT_STATUSES = {"selected", "rejected", "mixed", "failed", "timed_out"}
ALLOWED_PRIMITIVES = {"rmsnorm", "rope", "attention", "kv_decode"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _missing_fields(payload: dict[str, Any], required: set[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _looks_placeholder(value: Any) -> bool:
    return isinstance(value, str) and (not value.strip() or value.strip().startswith("<"))


def _almost_equal(left: Any, right: Any) -> bool:
    return _is_number(left) and _is_number(right) and abs(float(left) - float(right)) <= 1e-12


def _validate_budget(budget: Any) -> list[str]:
    if not isinstance(budget, dict):
        return ["search_budget must be an object"]
    errors: list[str] = []
    missing = _missing_fields(budget, REQUIRED_BUDGET)
    if missing:
        errors.append("search_budget missing fields: " + ", ".join(missing))
        return errors
    for field in ["agent_runs", "max_attempts_planned", "actual_attempts"]:
        if not isinstance(budget.get(field), int) or budget[field] < 1:
            errors.append(f"search_budget.{field} must be an integer >= 1")
    if not _is_number(budget.get("wall_clock_minutes")) or budget["wall_clock_minutes"] < 0:
        errors.append("search_budget.wall_clock_minutes must be a non-negative number")
    if not _non_empty_string(budget.get("local_hardware")):
        errors.append("search_budget.local_hardware must be a non-empty string")
    for field in ["network_used", "native_extension_used", "fixed_runner_feedback_used"]:
        if not isinstance(budget.get(field), bool):
            errors.append(f"search_budget.{field} must be boolean")
    if budget.get("fixed_runner_feedback_used") is not False:
        errors.append("search_budget.fixed_runner_feedback_used must be false before trusted replay")
    return errors


def _validate_selection(selection: Any) -> list[str]:
    if not isinstance(selection, dict):
        return ["candidate_selection must be an object"]
    errors: list[str] = []
    missing = _missing_fields(selection, REQUIRED_SELECTION)
    if missing:
        errors.append("candidate_selection missing fields: " + ", ".join(missing))
        return errors
    if _looks_placeholder(selection.get("selected_attempt_id")):
        errors.append("candidate_selection.selected_attempt_id must be concrete")
    if selection.get("selection_metric") != "public_geomean_runtime_ms":
        errors.append("candidate_selection.selection_metric must be public_geomean_runtime_ms")
    if selection.get("direction") != "minimize":
        errors.append("candidate_selection.direction must be minimize")
    for field in ["baseline_score", "selected_score"]:
        if not _is_number(selection.get(field)):
            errors.append(f"candidate_selection.{field} must be numeric")
    for field in ["selection_reason", "stopped_reason"]:
        if _looks_placeholder(selection.get(field)):
            errors.append(f"candidate_selection.{field} must be filled")
    if selection.get("selected_after_seeing_hidden_cases") is not False:
        errors.append("candidate_selection.selected_after_seeing_hidden_cases must be false")
    return errors


def _validate_attempt(attempt: Any, index: int) -> list[str]:
    prefix = f"attempts[{index}]"
    if not isinstance(attempt, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    missing = _missing_fields(attempt, REQUIRED_ATTEMPT)
    if missing:
        errors.append(f"{prefix} missing fields: " + ", ".join(missing))
        return errors
    if _looks_placeholder(attempt.get("id")):
        errors.append(f"{prefix}.id must be concrete")
    if attempt.get("status") not in ALLOWED_ATTEMPT_STATUSES:
        errors.append(f"{prefix}.status must be one of {sorted(ALLOWED_ATTEMPT_STATUSES)}")
    if attempt.get("primitive") not in ALLOWED_PRIMITIVES:
        errors.append(f"{prefix}.primitive must be one of {sorted(ALLOWED_PRIMITIVES)}")
    for field in ["hypothesis", "command", "backend", "result_summary"]:
        if _looks_placeholder(attempt.get(field)):
            errors.append(f"{prefix}.{field} must be filled")
    if not _non_empty_string_list(attempt.get("changed_files")):
        errors.append(f"{prefix}.changed_files must be a non-empty list")
    if not _non_empty_string_list(attempt.get("failure_modes")):
        errors.append(f"{prefix}.failure_modes must be a non-empty list")
    for field in ["public_geomean_runtime_ms", "reference_public_geomean_runtime_ms"]:
        if not _is_number(attempt.get(field)):
            errors.append(f"{prefix}.{field} must be numeric")
    for field in ["correct", "public_stress_correct", "invariant_probes_passed"]:
        if not isinstance(attempt.get(field), bool):
            errors.append(f"{prefix}.{field} must be boolean")
    if "hidden" in attempt:
        errors.append(f"{prefix} must not include hidden feedback fields")
    return errors


def validate_ledger(ledger: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing_fields(ledger, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("search ledger missing fields: " + ", ".join(missing))
        return errors
    if ledger.get("challenge") != "limes-kernelforge":
        errors.append("search ledger challenge must be limes-kernelforge")
    for field in ["submission_id", "ledger_id", "source"]:
        if _looks_placeholder(ledger.get(field)):
            errors.append(f"{field} must be concrete")

    errors.extend(_validate_budget(ledger.get("search_budget")))
    errors.extend(_validate_selection(ledger.get("candidate_selection")))

    attempts = ledger.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        errors.append("attempts must be a non-empty list")
        attempts = []
    selected_count = 0
    attempt_ids: set[str] = set()
    selected_attempt: dict[str, Any] | None = None
    for index, attempt in enumerate(attempts):
        errors.extend(_validate_attempt(attempt, index))
        if isinstance(attempt, dict):
            attempt_id = attempt.get("id")
            if isinstance(attempt_id, str):
                if attempt_id in attempt_ids:
                    errors.append(f"attempts[{index}].id duplicates an earlier attempt")
                attempt_ids.add(attempt_id)
            if attempt.get("status") == "selected":
                selected_count += 1
                selected_attempt = attempt
    if selected_count != 1:
        errors.append("search ledger must contain exactly one selected attempt")

    budget = ledger.get("search_budget", {})
    if isinstance(budget, dict) and isinstance(budget.get("actual_attempts"), int):
        if budget["actual_attempts"] != len(attempts):
            errors.append("search_budget.actual_attempts must equal attempts length")
        if isinstance(budget.get("max_attempts_planned"), int) and budget["actual_attempts"] > budget["max_attempts_planned"]:
            errors.append("search_budget.actual_attempts must not exceed max_attempts_planned")

    selection = ledger.get("candidate_selection", {})
    if isinstance(selection, dict):
        selected_attempt_id = selection.get("selected_attempt_id")
        if selected_attempt_id not in attempt_ids:
            errors.append("candidate_selection.selected_attempt_id must match an attempt id")
        if selected_attempt is not None:
            if not _almost_equal(selection.get("selected_score"), selected_attempt.get("public_geomean_runtime_ms")):
                errors.append("candidate_selection.selected_score must match selected attempt public_geomean_runtime_ms")
            if not _almost_equal(selection.get("baseline_score"), selected_attempt.get("reference_public_geomean_runtime_ms")):
                errors.append("candidate_selection.baseline_score must match selected attempt reference_public_geomean_runtime_ms")
            if selected_attempt.get("correct") is not True:
                errors.append("selected attempt must be correct")
            if selected_attempt.get("public_stress_correct") is not True:
                errors.append("selected attempt must pass public stress correctness")
            if selected_attempt.get("invariant_probes_passed") is not True:
                errors.append("selected attempt must pass invariant probes")

    boundary = ledger.get("public_data_boundary")
    if not isinstance(boundary, dict):
        errors.append("public_data_boundary must be an object")
    else:
        missing_boundary = _missing_fields(boundary, REQUIRED_BOUNDARY)
        if missing_boundary:
            errors.append("public_data_boundary missing fields: " + ", ".join(missing_boundary))
        if boundary.get("used_hidden_cases") is not False:
            errors.append("public_data_boundary.used_hidden_cases must be false")
        if boundary.get("used_private_runner_feedback") is not False:
            errors.append("public_data_boundary.used_private_runner_feedback must be false")
        if boundary.get("public_timings_candidate_only") is not True:
            errors.append("public_data_boundary.public_timings_candidate_only must be true")

    replay_request = ledger.get("replay_request")
    if not isinstance(replay_request, dict):
        errors.append("replay_request must be an object")
    else:
        missing_replay = _missing_fields(replay_request, REQUIRED_REPLAY)
        if missing_replay:
            errors.append("replay_request missing fields: " + ", ".join(missing_replay))
        if not isinstance(replay_request.get("requested"), bool):
            errors.append("replay_request.requested must be boolean")
        if _looks_placeholder(replay_request.get("runner_track")):
            errors.append("replay_request.runner_track must be filled")
        if _looks_placeholder(replay_request.get("rationale")):
            errors.append("replay_request.rationale must be filled")

    if not _non_empty_string_list(ledger.get("negative_or_mixed_findings")):
        errors.append("negative_or_mixed_findings must be a non-empty list")
    return errors
