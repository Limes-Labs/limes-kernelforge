from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harness.invariant_probes import run_invariant_probes
from harness.local_bundle_guard import SKIPPED_PUBLIC_SCORE_FIELDS, STABLE_PUBLIC_SCORE_FIELDS
from harness.public_audit import run_public_audit
from harness.score import public_score


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASELINE = ROOT / "baselines" / "public-smoke-baseline.json"
SCHEMA_VERSION = "0.1.0"
BASELINE_KIND = "public-smoke-contract"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_value(expected: Any, actual: Any) -> bool:
    if _is_number(expected) and _is_number(actual):
        return abs(float(expected) - float(actual)) <= 1e-12
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            return False
        return all(_same_value(expected[key], actual[key]) for key in expected)
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        return all(_same_value(left, right) for left, right in zip(expected, actual))
    return expected == actual


def _probe_summary(report: dict[str, Any]) -> dict[str, Any]:
    probes = report.get("probes", [])
    return {
        "ok": report.get("ok"),
        "probe_count": report.get("probe_count"),
        "probe_names": sorted(
            probe.get("name")
            for probe in probes
            if isinstance(probe, dict) and isinstance(probe.get("name"), str)
        ),
    }


def _audit_summary(report: dict[str, Any]) -> dict[str, Any]:
    audits = report.get("audits", [])
    return {
        "ok": report.get("ok"),
        "audit_count": report.get("audit_count"),
        "audit_names": sorted(
            audit.get("name")
            for audit in audits
            if isinstance(audit, dict) and isinstance(audit.get("name"), str)
        ),
    }


def current_public_baseline() -> dict[str, Any]:
    score = public_score()
    probes = run_invariant_probes()
    audit = run_public_audit()
    return {
        "schema_version": SCHEMA_VERSION,
        "challenge": "limes-kernelforge",
        "baseline_kind": BASELINE_KIND,
        "description": "Locks stable public smoke fields for benchmark drift checks; local timing fields are intentionally excluded.",
        "score_fields": {
            field: score.get(field)
            for field in STABLE_PUBLIC_SCORE_FIELDS
        },
        "skipped_score_fields": SKIPPED_PUBLIC_SCORE_FIELDS,
        "invariant_probes": _probe_summary(probes),
        "public_audit": _audit_summary(audit),
    }


def validate_public_baseline(
    expected: dict[str, Any],
    current: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if current is None:
        current = current_public_baseline()
    errors: list[str] = []
    for field, expected_value in [
        ("schema_version", SCHEMA_VERSION),
        ("challenge", "limes-kernelforge"),
        ("baseline_kind", BASELINE_KIND),
    ]:
        if expected.get(field) != expected_value:
            errors.append(f"baseline {field} must be {expected_value!r}")

    expected_score = expected.get("score_fields")
    current_score = current.get("score_fields")
    if not isinstance(expected_score, dict):
        errors.append("baseline score_fields must be an object")
        expected_score = {}
    if not isinstance(current_score, dict):
        errors.append("current score_fields must be an object")
        current_score = {}
    expected_keys = set(expected_score)
    current_keys = set(current_score)
    required_keys = set(STABLE_PUBLIC_SCORE_FIELDS)
    if expected_keys != required_keys:
        errors.append("baseline score_fields keys do not match stable public score fields")
    if current_keys != required_keys:
        errors.append("current score_fields keys do not match stable public score fields")
    for field in sorted(required_keys):
        if field in expected_score and field in current_score and not _same_value(expected_score[field], current_score[field]):
            errors.append(
                f"public baseline drift in score_fields.{field}: "
                f"expected {expected_score[field]!r}, got {current_score[field]!r}"
            )

    for field in ["skipped_score_fields", "invariant_probes", "public_audit"]:
        if not _same_value(expected.get(field), current.get(field)):
            errors.append(
                f"public baseline drift in {field}: expected {expected.get(field)!r}, got {current.get(field)!r}"
            )

    return {
        "ok": not errors,
        "challenge": current.get("challenge"),
        "baseline_kind": current.get("baseline_kind"),
        "baseline": str(DEFAULT_BASELINE),
        "compared_score_fields": STABLE_PUBLIC_SCORE_FIELDS,
        "skipped_score_fields": SKIPPED_PUBLIC_SCORE_FIELDS,
        "errors": errors,
    }


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
