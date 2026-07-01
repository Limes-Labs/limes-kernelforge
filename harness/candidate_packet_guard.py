from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from harness.agent_notes_guard import validate_notes
from harness.local_bundle_guard import validate_local_bundle
from harness.search_ledger_guard import validate_ledger
from harness.source_bundle_guard import validate_source_bundle
from harness.submission_guard import load_json, validate_manifest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "0.1.0"
PACKET_KIND = "local-candidate-packet"
CHALLENGE = "limes-kernelforge"
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "challenge",
    "packet_kind",
    "source",
    "packet_id",
    "status",
    "commit",
    "candidate_ready",
    "artifacts",
    "evidence",
    "local_metrics",
    "gates",
}
REQUIRED_ARTIFACTS = {
    "submission_manifest",
    "source_bundle",
    "search_ledger",
    "agent_notes",
    "public_score",
    "invariant_probes",
    "public_audit",
}
REQUIRED_ARTIFACT_FIELDS = {"path", "sha256", "validated"}
REQUIRED_EVIDENCE = {
    "submission_manifest_validated",
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
    "public_timings_candidate_only",
}
REQUIRED_LOCAL_METRICS = {
    "correct",
    "primary_correct",
    "public_stress_correct",
    "max_abs_error",
    "max_rel_error",
    "public_geomean_runtime_ms",
    "reference_public_geomean_runtime_ms",
    "public_speedup_vs_reference",
    "backend",
    "source_bundle_sha256",
}


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_path(path_text: str, root: Path = ROOT) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return root / path


def artifact_record(path: Path, root: Path = ROOT, validated: bool = True) -> dict[str, Any]:
    display = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    return {
        "path": display,
        "sha256": sha256_file(path),
        "validated": validated,
    }


def _is_example(packet: dict[str, Any]) -> bool:
    return packet.get("source") == "example-schema-only"


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _looks_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value.lower()
    )


def _almost_equal(left: Any, right: Any) -> bool:
    return (
        isinstance(left, (int, float))
        and not isinstance(left, bool)
        and isinstance(right, (int, float))
        and not isinstance(right, bool)
        and abs(float(left) - float(right)) <= 1e-12
    )


def _artifact_errors(artifacts: Any, root: Path, verify_files: bool, example: bool) -> list[str]:
    if not isinstance(artifacts, dict):
        return ["artifacts must be an object"]
    errors: list[str] = []
    missing = sorted(REQUIRED_ARTIFACTS.difference(artifacts))
    if missing:
        errors.append("artifacts missing fields: " + ", ".join(missing))
    for name in sorted(REQUIRED_ARTIFACTS.intersection(artifacts)):
        artifact = artifacts.get(name)
        if not isinstance(artifact, dict):
            errors.append(f"artifacts.{name} must be an object")
            continue
        missing_fields = sorted(REQUIRED_ARTIFACT_FIELDS.difference(artifact))
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


def _load_artifact(packet: dict[str, Any], name: str, root: Path) -> dict[str, Any]:
    artifact = packet["artifacts"][name]
    return load_json(resolve_path(artifact["path"], root))


def _validate_real_artifacts(packet: dict[str, Any], contract: dict[str, Any], root: Path) -> list[str]:
    errors: list[str] = []
    manifest = _load_artifact(packet, "submission_manifest", root)
    source_bundle = _load_artifact(packet, "source_bundle", root)
    search_ledger = _load_artifact(packet, "search_ledger", root)
    agent_notes = _load_artifact(packet, "agent_notes", root)
    public_score = _load_artifact(packet, "public_score", root)
    invariant_probes = _load_artifact(packet, "invariant_probes", root)
    public_audit = _load_artifact(packet, "public_audit", root)

    changed_files = manifest.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []

    submission_errors = validate_manifest(manifest, contract)
    source_errors = validate_source_bundle(
        source_bundle,
        contract,
        root=root,
        changed_paths=changed_files,
        source_commit=manifest.get("commit"),
    )["errors"]
    ledger_errors = validate_ledger(search_ledger)
    notes_errors = validate_notes(agent_notes)
    local_bundle_errors = validate_local_bundle(
        manifest=manifest,
        contract=contract,
        changed_paths=changed_files,
        search_ledger=search_ledger,
        source_bundle=source_bundle,
    )["errors"]

    for prefix, nested_errors in [
        ("submission_manifest", submission_errors),
        ("source_bundle", source_errors),
        ("search_ledger", ledger_errors),
        ("agent_notes", notes_errors),
        ("local_bundle", local_bundle_errors),
    ]:
        errors.extend(f"{prefix}: {error}" for error in nested_errors)

    if invariant_probes.get("ok") is not True:
        errors.append("invariant_probes.ok must be true")
    if public_audit.get("ok") is not True:
        errors.append("public_audit.ok must be true")
    if not isinstance(public_score, dict):
        errors.append("public_score artifact must be an object")
    if public_score.get("correct") is not True:
        errors.append("public_score.correct must be true")
    if public_score.get("public_stress_correct") is not True:
        errors.append("public_score.public_stress_correct must be true")

    metrics = packet.get("local_metrics", {})
    if isinstance(metrics, dict):
        comparisons = {
            "max_abs_error": public_score.get("max_abs_error"),
            "max_rel_error": public_score.get("max_rel_error"),
            "public_geomean_runtime_ms": public_score.get("public_geomean_runtime_ms"),
            "reference_public_geomean_runtime_ms": public_score.get("reference_public_geomean_runtime_ms"),
            "public_speedup_vs_reference": public_score.get("public_speedup_vs_reference"),
        }
        for field, expected in comparisons.items():
            if field in metrics and not _almost_equal(metrics[field], expected):
                errors.append(f"local_metrics.{field} must match public_score.{field}")
        for field in ["correct", "primary_correct", "public_stress_correct", "backend"]:
            if field in metrics and metrics[field] != public_score.get(field):
                errors.append(f"local_metrics.{field} must match public_score.{field}")
        if metrics.get("source_bundle_sha256") != source_bundle.get("bundle_sha256"):
            errors.append("local_metrics.source_bundle_sha256 must match source bundle")

    artifact_validations = {
        "submission_manifest": not submission_errors,
        "source_bundle": not source_errors,
        "search_ledger": not ledger_errors,
        "agent_notes": not notes_errors,
        "public_score": isinstance(public_score, dict) and public_score.get("correct") is True,
        "invariant_probes": invariant_probes.get("ok") is True,
        "public_audit": public_audit.get("ok") is True,
    }
    for name, expected in artifact_validations.items():
        actual = packet["artifacts"][name].get("validated")
        if actual is not expected:
            errors.append(f"artifacts.{name}.validated must be {expected}")

    evidence = packet.get("evidence", {})
    evidence_expectations = {
        "submission_manifest_validated": not submission_errors,
        "source_bundle_validated": not source_errors,
        "search_ledger_validated": not ledger_errors,
        "agent_notes_validated": not notes_errors,
        "public_score_present": isinstance(public_score, dict),
        "public_correctness_passed": public_score.get("correct") is True,
        "public_stress_correctness_passed": public_score.get("public_stress_correct") is True,
        "invariant_probes_passed": invariant_probes.get("ok") is True,
        "public_audit_passed": public_audit.get("ok") is True,
        "local_bundle_validated": not local_bundle_errors,
    }
    if isinstance(evidence, dict):
        for field, expected in evidence_expectations.items():
            if evidence.get(field) is not expected:
                errors.append(f"evidence.{field} must be {expected}")
    return errors


def validate_packet(
    packet: dict[str, Any],
    contract: dict[str, Any],
    root: Path = ROOT,
    verify_files: bool = True,
) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL.difference(packet))
    if missing:
        errors.append("candidate packet missing fields: " + ", ".join(missing))
        return errors

    example = _is_example(packet)
    if packet.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if packet.get("challenge") != CHALLENGE or packet.get("challenge") != contract.get("id"):
        errors.append(f"challenge must be {CHALLENGE}")
    if packet.get("packet_kind") != PACKET_KIND:
        errors.append(f"packet_kind must be {PACKET_KIND}")
    if packet.get("status") != "candidate":
        errors.append("status must be candidate")
    if not _non_empty_string(packet.get("packet_id")):
        errors.append("packet_id must be a non-empty string")
    if not example and not _non_empty_string(packet.get("commit")):
        errors.append("commit must be concrete")
    if example:
        disclaimer = str(packet.get("disclaimer", "")).lower()
        if "not a real candidate" not in disclaimer:
            errors.append("example candidate packet disclaimer must say it is not a real candidate")
        if packet.get("candidate_ready") is not False:
            errors.append("example candidate packet must not be candidate_ready")

    errors.extend(_artifact_errors(packet.get("artifacts"), root, verify_files, example))

    evidence = packet.get("evidence")
    if not isinstance(evidence, dict):
        errors.append("evidence must be an object")
    else:
        missing_evidence = sorted(REQUIRED_EVIDENCE.difference(evidence))
        if missing_evidence:
            errors.append("evidence missing fields: " + ", ".join(missing_evidence))
        for field in REQUIRED_EVIDENCE:
            if field in evidence and not isinstance(evidence[field], bool):
                errors.append(f"evidence.{field} must be boolean")
        if evidence.get("public_timings_candidate_only") is not True:
            errors.append("evidence.public_timings_candidate_only must be true")

    metrics = packet.get("local_metrics")
    if not isinstance(metrics, dict):
        errors.append("local_metrics must be an object")
    else:
        missing_metrics = sorted(REQUIRED_LOCAL_METRICS.difference(metrics))
        if missing_metrics:
            errors.append("local_metrics missing fields: " + ", ".join(missing_metrics))

    gates = packet.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        for field in ["passed", "failed", "blocked"]:
            if not isinstance(gates.get(field), list):
                errors.append(f"gates.{field} must be a list")
        if packet.get("candidate_ready") is True and gates.get("failed"):
            errors.append("candidate_ready packets must not have failed gates")

    if verify_files and not example and not errors:
        errors.extend(_validate_real_artifacts(packet, contract, root))

    if not example and isinstance(evidence, dict):
        ready = all(evidence.get(field) is True for field in REQUIRED_EVIDENCE)
        if packet.get("candidate_ready") is not ready:
            errors.append(f"candidate_ready must be {ready}")
    return errors


def build_candidate_packet(
    contract: dict[str, Any],
    manifest_path: Path,
    source_bundle_path: Path,
    search_ledger_path: Path,
    agent_notes_path: Path,
    public_score_path: Path,
    invariant_probes_path: Path,
    public_audit_path: Path,
    packet_id: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    manifest = load_json(manifest_path)
    source_bundle = load_json(source_bundle_path)
    search_ledger = load_json(search_ledger_path)
    agent_notes = load_json(agent_notes_path)
    public_score = load_json(public_score_path)
    invariant_probes = load_json(invariant_probes_path)
    public_audit = load_json(public_audit_path)
    changed_files = manifest.get("changed_files", [])
    if not isinstance(changed_files, list):
        changed_files = []

    submission_errors = validate_manifest(manifest, contract)
    source_errors = validate_source_bundle(
        source_bundle,
        contract,
        root=root,
        changed_paths=changed_files,
        source_commit=manifest.get("commit"),
    )["errors"]
    ledger_errors = validate_ledger(search_ledger)
    notes_errors = validate_notes(agent_notes)
    local_bundle_errors = validate_local_bundle(
        manifest=manifest,
        contract=contract,
        changed_paths=changed_files,
        search_ledger=search_ledger,
        source_bundle=source_bundle,
    )["errors"]

    artifacts = {
        "submission_manifest": artifact_record(manifest_path, root, not submission_errors),
        "source_bundle": artifact_record(source_bundle_path, root, not source_errors),
        "search_ledger": artifact_record(search_ledger_path, root, not ledger_errors),
        "agent_notes": artifact_record(agent_notes_path, root, not notes_errors),
        "public_score": artifact_record(public_score_path, root, isinstance(public_score, dict) and public_score.get("correct") is True),
        "invariant_probes": artifact_record(invariant_probes_path, root, invariant_probes.get("ok") is True),
        "public_audit": artifact_record(public_audit_path, root, public_audit.get("ok") is True),
    }
    evidence = {
        "submission_manifest_validated": not submission_errors,
        "source_bundle_validated": not source_errors,
        "search_ledger_validated": not ledger_errors,
        "agent_notes_validated": not notes_errors,
        "public_score_present": isinstance(public_score, dict),
        "public_correctness_passed": public_score.get("correct") is True,
        "public_stress_correctness_passed": public_score.get("public_stress_correct") is True,
        "invariant_probes_passed": invariant_probes.get("ok") is True,
        "public_audit_passed": public_audit.get("ok") is True,
        "local_bundle_validated": not local_bundle_errors,
        "no_forbidden_paths": not submission_errors,
        "public_timings_candidate_only": True,
    }
    failed = [
        name
        for name, passed in evidence.items()
        if passed is not True
    ]
    packet = {
        "schema_version": SCHEMA_VERSION,
        "challenge": CHALLENGE,
        "packet_kind": PACKET_KIND,
        "source": "local-candidate",
        "packet_id": packet_id,
        "status": "candidate",
        "commit": manifest.get("commit"),
        "candidate_ready": not failed,
        "artifacts": artifacts,
        "evidence": evidence,
        "local_metrics": {
            "correct": public_score.get("correct"),
            "primary_correct": public_score.get("primary_correct"),
            "public_stress_correct": public_score.get("public_stress_correct"),
            "max_abs_error": public_score.get("max_abs_error"),
            "max_rel_error": public_score.get("max_rel_error"),
            "public_geomean_runtime_ms": public_score.get("public_geomean_runtime_ms"),
            "reference_public_geomean_runtime_ms": public_score.get("reference_public_geomean_runtime_ms"),
            "public_speedup_vs_reference": public_score.get("public_speedup_vs_reference"),
            "backend": public_score.get("backend"),
            "source_bundle_sha256": source_bundle.get("bundle_sha256"),
        },
        "gates": {
            "passed": [name for name, passed in evidence.items() if passed is True],
            "failed": failed,
            "blocked": ["fixed runner replay not run", "hidden shape verifier not run"],
        },
    }
    return packet
