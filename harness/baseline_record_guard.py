from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


VALID_BASELINE_STATUSES = {"example", "pending-freeze", "frozen"}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "source",
    "baseline_id",
    "baseline_status",
    "runner_id",
    "runner_track",
    "runner_manifest_hash",
    "dependency_lock_digest",
    "case_suite_hash",
    "code_hash",
    "primary_metric",
    "direction",
    "tolerance",
    "timing_policy",
    "aggregate",
    "case_results",
    "replay_constraints",
    "promotion_use",
}
REQUIRED_AGGREGATE = {
    "reference_hidden_geomean_runtime_ms",
    "max_abs_error",
    "max_rel_error",
    "peak_memory_mb",
    "case_count",
    "correct",
}
REQUIRED_CASE_RESULT = {
    "primitive",
    "case_id",
    "reference_runtime_ms",
    "max_abs_error",
    "max_rel_error",
    "correct",
}
REQUIRED_REPLAY_CONSTRAINTS = {
    "clean_checkout",
    "network_disabled",
    "candidate_selection_uses_hidden_cases",
    "hidden_shapes_disclosed_before_candidate_freeze",
    "correctness_first",
}
REQUIRED_PROMOTION_USE = {
    "used_for_promoted_comparison",
    "comparison_metric",
    "baseline_metric",
    "direction",
    "runner_track",
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


def _almost_equal(left: Any, right: Any) -> bool:
    return _is_number(left) and _is_number(right) and abs(float(left) - float(right)) <= 1e-12


def _runner_track_ids(contract: dict[str, Any]) -> set[str]:
    return {track["id"] for track in contract.get("runner_tracks", []) if isinstance(track, dict)}


def _geomean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def validate_record(record: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = _missing_fields(record, REQUIRED_TOP_LEVEL)
    if missing:
        errors.append("baseline record missing fields: " + ", ".join(missing))
        return errors

    if record.get("challenge") != contract.get("challenge"):
        errors.append("baseline record challenge does not match verifier contract")
    if record.get("source") == "example-schema-only":
        disclaimer = str(record.get("disclaimer", "")).lower()
        if "not an official baseline" not in disclaimer:
            errors.append("example baseline record disclaimer must say it is not an official baseline")
    if record.get("baseline_status") not in VALID_BASELINE_STATUSES:
        errors.append("baseline_status must be example, pending-freeze, or frozen")
    if record.get("primary_metric") != contract.get("official_primary_metric"):
        errors.append("primary_metric must match verifier contract official_primary_metric")
    if record.get("direction") != contract.get("score_direction"):
        errors.append("direction must match verifier contract score_direction")
    if record.get("runner_track") not in _runner_track_ids(contract):
        errors.append("runner_track must be a known fixed runner track")

    for field in [
        "baseline_id",
        "runner_id",
        "runner_manifest_hash",
        "dependency_lock_digest",
        "case_suite_hash",
        "code_hash",
    ]:
        if not _non_empty_string(record.get(field)):
            errors.append(f"{field} must be a non-empty string")

    tolerance = _require_object(record, "tolerance", errors)
    tolerance_matrix = contract.get("tolerance_matrix", {})
    for dtype, expected in tolerance_matrix.items():
        if tolerance.get(dtype) != expected:
            errors.append(f"tolerance.{dtype} must match verifier contract tolerance_matrix")

    timing_policy = _require_object(record, "timing_policy", errors)
    contract_timing = contract.get("timing_policy", {})
    for field in ["aggregation", "timer", "memory_cap"]:
        if timing_policy.get(field) != contract_timing.get(field):
            errors.append(f"timing_policy.{field} must match verifier contract")
    if timing_policy.get("hardware_fingerprint_required") is not True:
        errors.append("timing_policy.hardware_fingerprint_required must be true")

    aggregate = _require_object(record, "aggregate", errors)
    missing_aggregate = _missing_fields(aggregate, REQUIRED_AGGREGATE)
    if missing_aggregate:
        errors.append("aggregate missing fields: " + ", ".join(missing_aggregate))
    for field in ["reference_hidden_geomean_runtime_ms", "max_abs_error", "max_rel_error", "peak_memory_mb"]:
        if field in aggregate and not _is_number(aggregate[field]):
            errors.append(f"aggregate.{field} must be numeric")
    if aggregate.get("correct") is not True:
        errors.append("aggregate.correct must be true")
    if "case_count" in aggregate and (not isinstance(aggregate["case_count"], int) or aggregate["case_count"] <= 0):
        errors.append("aggregate.case_count must be a positive integer")

    case_results = _require_list(record, "case_results", errors)
    if aggregate.get("case_count") != len(case_results):
        errors.append("aggregate.case_count must match case_results length")
    runtimes: list[float] = []
    for index, result in enumerate(case_results):
        if not isinstance(result, dict):
            errors.append(f"case_results[{index}] must be an object")
            continue
        missing_result = _missing_fields(result, REQUIRED_CASE_RESULT)
        if missing_result:
            errors.append(f"case_results[{index}] missing fields: " + ", ".join(missing_result))
        for field in ["primitive", "case_id"]:
            if not _non_empty_string(result.get(field)):
                errors.append(f"case_results[{index}].{field} must be a non-empty string")
        for field in ["reference_runtime_ms", "max_abs_error", "max_rel_error"]:
            if field in result and not _is_number(result[field]):
                errors.append(f"case_results[{index}].{field} must be numeric")
        if result.get("correct") is not True:
            errors.append(f"case_results[{index}].correct must be true")
        if _is_number(result.get("reference_runtime_ms")) and result["reference_runtime_ms"] > 0:
            runtimes.append(float(result["reference_runtime_ms"]))
    if len(runtimes) == len(case_results) and not _almost_equal(
        _geomean(runtimes),
        aggregate.get("reference_hidden_geomean_runtime_ms"),
    ):
        errors.append("aggregate.reference_hidden_geomean_runtime_ms must equal geomean case runtime")

    replay_constraints = _require_object(record, "replay_constraints", errors)
    missing_constraints = _missing_fields(replay_constraints, REQUIRED_REPLAY_CONSTRAINTS)
    if missing_constraints:
        errors.append("replay_constraints missing fields: " + ", ".join(missing_constraints))
    if replay_constraints.get("clean_checkout") is not True:
        errors.append("replay_constraints.clean_checkout must be true")
    if replay_constraints.get("network_disabled") is not True:
        errors.append("replay_constraints.network_disabled must be true")
    if replay_constraints.get("candidate_selection_uses_hidden_cases") is not False:
        errors.append("replay_constraints.candidate_selection_uses_hidden_cases must be false")
    if replay_constraints.get("hidden_shapes_disclosed_before_candidate_freeze") is not False:
        errors.append("replay_constraints.hidden_shapes_disclosed_before_candidate_freeze must be false")
    if replay_constraints.get("correctness_first") is not True:
        errors.append("replay_constraints.correctness_first must be true")

    promotion_use = _require_object(record, "promotion_use", errors)
    missing_promotion = _missing_fields(promotion_use, REQUIRED_PROMOTION_USE)
    if missing_promotion:
        errors.append("promotion_use missing fields: " + ", ".join(missing_promotion))
    if promotion_use.get("comparison_metric") != contract.get("official_primary_metric"):
        errors.append("promotion_use.comparison_metric must match official primary metric")
    if promotion_use.get("baseline_metric") != "reference_hidden_geomean_runtime_ms":
        errors.append("promotion_use.baseline_metric must be reference_hidden_geomean_runtime_ms")
    if promotion_use.get("direction") != contract.get("score_direction"):
        errors.append("promotion_use.direction must match score direction")
    if promotion_use.get("runner_track") != record.get("runner_track"):
        errors.append("promotion_use.runner_track must match runner_track")
    if promotion_use.get("used_for_promoted_comparison") is True and record.get("baseline_status") != "frozen":
        errors.append("used_for_promoted_comparison requires baseline_status frozen")

    return errors
