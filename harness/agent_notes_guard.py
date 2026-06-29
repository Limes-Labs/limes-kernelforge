from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_SCORE_FIELDS = {
    "correct",
    "max_abs_error",
    "max_rel_error",
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_speedup_vs_reference",
    "backend",
}
REQUIRED_ATTEMPT_FIELDS = {
    "id",
    "status",
    "primitive",
    "hypothesis",
    "changed_files",
    "command",
    "public_score",
    "timing_variance_note",
    "result_summary",
    "failure_modes",
}
ALLOWED_ATTEMPT_STATUSES = {"selected", "rejected", "mixed", "failed", "timed_out"}
ALLOWED_PRIMITIVES = {"rmsnorm", "rope", "attention", "kv_decode"}


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _looks_placeholder(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return not stripped or stripped.startswith("<") or "describe" in stripped.lower()


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def _validate_public_score(score: Any, prefix: str) -> list[str]:
    if not isinstance(score, dict):
        return [f"{prefix}.public_score must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_SCORE_FIELDS.difference(score))
    if missing:
        errors.append(f"{prefix}.public_score missing fields: {', '.join(missing)}")
    if score.get("correct") is not True:
        errors.append(f"{prefix}.public_score.correct must be true for selected candidates")
    return errors


def _validate_attempt(attempt: Any, index: int) -> list[str]:
    prefix = f"attempts[{index}]"
    if not isinstance(attempt, dict):
        return [f"{prefix} must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_ATTEMPT_FIELDS.difference(attempt))
    if missing:
        errors.append(f"{prefix} missing fields: {', '.join(missing)}")
        return errors
    if _looks_placeholder(attempt.get("id")):
        errors.append(f"{prefix}.id must be concrete")
    if attempt.get("status") not in ALLOWED_ATTEMPT_STATUSES:
        errors.append(f"{prefix}.status must be one of {sorted(ALLOWED_ATTEMPT_STATUSES)}")
    if attempt.get("primitive") not in ALLOWED_PRIMITIVES:
        errors.append(f"{prefix}.primitive must be one of {sorted(ALLOWED_PRIMITIVES)}")
    for field in ("hypothesis", "command", "timing_variance_note", "result_summary"):
        if _looks_placeholder(attempt.get(field)):
            errors.append(f"{prefix}.{field} must be filled")
    changed_files = attempt.get("changed_files")
    if not _non_empty_string_list(changed_files):
        errors.append(f"{prefix}.changed_files must be a non-empty list of paths")
    failure_modes = attempt.get("failure_modes")
    if not _non_empty_string_list(failure_modes):
        errors.append(f"{prefix}.failure_modes must be a non-empty list")
    errors.extend(_validate_public_score(attempt.get("public_score"), prefix))
    return errors


def validate_notes(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("challenge") != "limes-kernelforge":
        errors.append("agent notes challenge must be limes-kernelforge")
    if _looks_placeholder(payload.get("submission_id")):
        errors.append("agent notes submission_id must be concrete")

    selection_summary = payload.get("selection_summary")
    if not isinstance(selection_summary, dict):
        errors.append("selection_summary must be an object")
        selection_summary = {}
    selected_attempt_id = selection_summary.get("selected_attempt_id")
    if _looks_placeholder(selected_attempt_id):
        errors.append("selection_summary.selected_attempt_id must be concrete")
    if _looks_placeholder(selection_summary.get("selection_reason")):
        errors.append("selection_summary.selection_reason must be filled")
    if not _non_empty_string_list(selection_summary.get("hidden_shape_assumptions")):
        errors.append("selection_summary.hidden_shape_assumptions must be a non-empty list")
    if not _non_empty_string_list(selection_summary.get("numerical_risks")):
        errors.append("selection_summary.numerical_risks must be a non-empty list")

    attempts = payload.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return errors + ["attempts must be a non-empty list"]
    selected_count = 0
    rejected_or_mixed_count = 0
    attempt_ids: set[str] = set()
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
            elif attempt.get("status") in {"rejected", "mixed", "failed", "timed_out"}:
                rejected_or_mixed_count += 1

    if selected_count != 1:
        errors.append("agent notes must contain exactly one selected attempt")
    if selected_attempt_id not in attempt_ids:
        errors.append("selection_summary.selected_attempt_id must match an attempt id")
    if len(attempts) > 1 and rejected_or_mixed_count == 0:
        errors.append("multi-attempt notes must preserve at least one non-selected attempt")
    if not _non_empty_string_list(payload.get("negative_or_mixed_findings")):
        errors.append("negative_or_mixed_findings must be a non-empty list")
    return errors
