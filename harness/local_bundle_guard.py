from __future__ import annotations

from typing import Any

from harness.invariant_probes import run_invariant_probes
from harness.public_audit import run_public_audit
from harness.score import public_score
from harness.search_ledger_guard import validate_ledger
from harness.source_bundle_guard import validate_source_bundle
from harness.submission_guard import validate_submission


STABLE_PUBLIC_SCORE_FIELDS = [
    "correct",
    "primary_correct",
    "max_abs_error",
    "max_rel_error",
    "public_stress_correct",
    "public_stress_case_count",
    "public_stress_max_abs_error",
    "public_stress_max_rel_error",
    "backend",
    "tolerance",
]
SKIPPED_PUBLIC_SCORE_FIELDS = [
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_runtime_delta_ms",
    "public_speedup_vs_reference",
    "public_stress_geomean_runtime_ms",
    "reference_public_stress_geomean_runtime_ms",
    "public_stress_speedup_vs_reference",
]
LEDGER_MANIFEST_SCORE_FIELDS = [
    "correct",
    "public_stress_correct",
    "backend",
]


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _same_value(expected: Any, actual: Any) -> bool:
    if _is_number(expected) and _is_number(actual):
        return abs(float(expected) - float(actual)) <= 1e-12
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected) != set(actual):
            return False
        return all(_same_value(expected[key], actual[key]) for key in expected)
    return expected == actual


def _compare_public_score(manifest_score: Any, fresh_score: dict[str, Any]) -> list[str]:
    if not isinstance(manifest_score, dict):
        return ["manifest public_score must be an object before local bundle comparison"]
    errors: list[str] = []
    for field in STABLE_PUBLIC_SCORE_FIELDS:
        if field not in manifest_score:
            errors.append(f"manifest public_score missing stable field {field}")
            continue
        if not _same_value(fresh_score.get(field), manifest_score.get(field)):
            errors.append(
                "manifest public_score."
                f"{field} is stale or fabricated: expected {fresh_score.get(field)!r}, "
                f"got {manifest_score.get(field)!r}"
            )
    return errors


def _compare_invariant_probes(manifest_probes: Any, fresh_probes: dict[str, Any]) -> list[str]:
    if not isinstance(manifest_probes, dict):
        return ["manifest invariant_probes must be an object before local bundle comparison"]
    errors: list[str] = []
    if manifest_probes.get("ok") != fresh_probes.get("ok"):
        errors.append(
            "manifest invariant_probes.ok does not match a fresh probe run: "
            f"expected {fresh_probes.get('ok')!r}, got {manifest_probes.get('ok')!r}"
        )
    if manifest_probes.get("probe_count") != fresh_probes.get("probe_count"):
        errors.append(
            "manifest invariant_probes.probe_count does not match a fresh probe run: "
            f"expected {fresh_probes.get('probe_count')!r}, "
            f"got {manifest_probes.get('probe_count')!r}"
        )
    if fresh_probes.get("ok") is not True:
        errors.append("fresh invariant probes did not pass")
    return errors


def _selected_attempt(ledger: dict[str, Any]) -> dict[str, Any] | None:
    selection = ledger.get("candidate_selection", {})
    selected_id = selection.get("selected_attempt_id") if isinstance(selection, dict) else None
    attempts = ledger.get("attempts", [])
    if not isinstance(attempts, list):
        return None
    for attempt in attempts:
        if isinstance(attempt, dict) and attempt.get("id") == selected_id:
            return attempt
    return None


def _compare_search_ledger(ledger: Any, manifest_score: Any) -> list[str]:
    if not isinstance(ledger, dict):
        return ["search ledger JSON must be provided for local bundle validation"]
    errors = [f"search_ledger: {error}" for error in validate_ledger(ledger)]
    if not isinstance(manifest_score, dict) or errors:
        return errors

    selected_attempt = _selected_attempt(ledger)
    if selected_attempt is None:
        return errors
    for field in LEDGER_MANIFEST_SCORE_FIELDS:
        if not _same_value(selected_attempt.get(field), manifest_score.get(field)):
            errors.append(f"search_ledger selected attempt {field} must match manifest public_score.{field}")
    if selected_attempt.get("invariant_probes_passed") is not True:
        errors.append("search_ledger selected attempt must record invariant_probes_passed true")
    return errors


def validate_local_bundle(
    manifest: dict[str, Any],
    contract: dict[str, Any],
    changed_paths: list[str],
    search_ledger: dict[str, Any] | None,
    source_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    errors = validate_submission(manifest, contract, changed_paths)

    fresh_score = public_score()
    errors.extend(_compare_public_score(manifest.get("public_score"), fresh_score))

    fresh_probes = run_invariant_probes()
    errors.extend(_compare_invariant_probes(manifest.get("invariant_probes"), fresh_probes))
    fresh_audit = run_public_audit()
    for audit in fresh_audit.get("audits", []):
        if isinstance(audit, dict) and audit.get("ok") is not True:
            for error in audit.get("errors", []):
                errors.append(f"public_audit {audit.get('name')}: {error}")
    errors.extend(_compare_search_ledger(search_ledger, manifest.get("public_score")))
    if source_bundle is None:
        errors.append("source bundle JSON must be provided for local bundle validation")
    else:
        source_report = validate_source_bundle(
            bundle=source_bundle,
            contract=contract,
            changed_paths=changed_paths,
            source_commit=manifest.get("commit"),
        )
        errors.extend(f"source_bundle: {error}" for error in source_report["errors"])

    return {
        "ok": not errors,
        "challenge": contract.get("id"),
        "changed_files": changed_paths,
        "compared_public_score_fields": STABLE_PUBLIC_SCORE_FIELDS,
        "skipped_public_score_fields": SKIPPED_PUBLIC_SCORE_FIELDS,
        "fresh_public_score": {
            field: fresh_score.get(field)
            for field in STABLE_PUBLIC_SCORE_FIELDS
        },
        "fresh_invariant_probes": {
            "ok": fresh_probes.get("ok"),
            "probe_count": fresh_probes.get("probe_count"),
        },
        "fresh_public_audit": {
            "ok": fresh_audit.get("ok"),
            "audit_count": fresh_audit.get("audit_count"),
        },
        "source_bundle_sha256": (
            source_bundle.get("bundle_sha256")
            if isinstance(source_bundle, dict)
            else None
        ),
        "errors": errors,
    }
