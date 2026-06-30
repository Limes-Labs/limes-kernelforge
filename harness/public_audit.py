from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path
from typing import Any, Callable

from harness.scoring import ABS_TOL, REL_TOL, error_stats


ROOT = Path(__file__).resolve().parents[1]
SOLUTION_FILES = [
    ROOT / "solution" / "rmsnorm.py",
    ROOT / "solution" / "rope.py",
    ROOT / "solution" / "attention.py",
    ROOT / "solution" / "kv_decode.py",
]
FORBIDDEN_STATIC_PATTERNS = [
    "cases/public_smoke",
    "cases.json",
    "stress_cases.json",
    "hidden_cases",
    "score.json",
    "harness.reference",
    "from harness",
    "import harness",
    "PUBLIC_CASES",
    "PUBLIC_STRESS_CASES",
]


def _solution(name: str):
    return importlib.import_module(f"solution.{name}")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _negate(value: Any) -> Any:
    if isinstance(value, list):
        return [_negate(item) for item in value]
    return -float(value)


def _add_vector(matrix: list[list[float]], shift: list[float]) -> list[list[float]]:
    return [[float(value) + shift[index] for index, value in enumerate(row)] for row in matrix]


def _assert_close(actual: Any, expected: Any, label: str) -> tuple[float, float]:
    max_abs, max_rel = error_stats(actual, expected)
    if max_abs > ABS_TOL or max_rel > REL_TOL:
        raise AssertionError(
            f"{label} exceeded tolerance: max_abs_error={max_abs}, max_rel_error={max_rel}"
        )
    return max_abs, max_rel


def scan_forbidden_static_patterns(paths: list[Path] = SOLUTION_FILES) -> list[str]:
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_STATIC_PATTERNS:
            if pattern in text:
                errors.append(f"{_display_path(path)} contains forbidden public-boundary token {pattern!r}")
    return errors


def _audit_static_boundary() -> dict[str, Any]:
    errors = scan_forbidden_static_patterns()
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": [],
        "details": {
            "scanned_files": [str(path.relative_to(ROOT)) for path in SOLUTION_FILES],
            "forbidden_patterns": FORBIDDEN_STATIC_PATTERNS,
        },
    }


def _audit_rmsnorm_sign_symmetry() -> dict[str, Any]:
    solution = _solution("rmsnorm")
    x = [[1.25, -0.5, 3.0, -4.0], [-2.0, 0.0, 0.75, 8.0]]
    weight = [1.0, -0.5, 0.25, 2.0]
    positive = solution.rmsnorm(copy.deepcopy(x), list(weight), 1e-6)
    negative = solution.rmsnorm(_negate(copy.deepcopy(x)), list(weight), 1e-6)
    expected_negative = _negate(positive)
    max_abs, max_rel = _assert_close(negative, expected_negative, "rmsnorm sign symmetry")
    return {"ok": True, "errors": [], "warnings": [], "details": {"max_abs_error": max_abs, "max_rel_error": max_rel}}


def _pair_norms(matrix: list[list[float]]) -> list[list[float]]:
    return [
        [row[index] * row[index] + row[index + 1] * row[index + 1] for index in range(0, len(row), 2)]
        for row in matrix
    ]


def _audit_rope_identity_and_norm() -> dict[str, Any]:
    solution = _solution("rope")
    x = [[1.0, 2.0, -3.0, 0.5], [0.25, -0.75, 4.0, -1.5]]
    identity = solution.rope(copy.deepcopy(x), [0, 0], 10000.0)
    identity_abs, identity_rel = _assert_close(identity, x, "rope zero-position identity")
    rotated = solution.rope(copy.deepcopy(x), [3, 17], 10000.0)
    norm_abs, norm_rel = _assert_close(_pair_norms(rotated), _pair_norms(x), "rope pair-norm preservation")
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "details": {
            "identity_max_abs_error": identity_abs,
            "identity_max_rel_error": identity_rel,
            "norm_max_abs_error": norm_abs,
            "norm_max_rel_error": norm_rel,
        },
    }


def _audit_attention_value_shift() -> dict[str, Any]:
    solution = _solution("attention")
    q = [[1.0, 0.0], [0.5, 1.0], [-0.25, 0.75]]
    k = [[0.5, 0.25], [1.0, -0.5], [0.0, 1.5]]
    v = [[2.0, -1.0], [3.0, 4.0], [-2.0, 5.0]]
    shift = [7.0, -3.0]
    base = solution.causal_attention_prefill(copy.deepcopy(q), copy.deepcopy(k), copy.deepcopy(v))
    shifted = solution.causal_attention_prefill(copy.deepcopy(q), copy.deepcopy(k), _add_vector(v, shift))
    expected = _add_vector(base, shift)
    max_abs, max_rel = _assert_close(shifted, expected, "attention value-shift invariance")
    return {"ok": True, "errors": [], "warnings": [], "details": {"max_abs_error": max_abs, "max_rel_error": max_rel}}


def _audit_kv_decode_value_shift() -> dict[str, Any]:
    solution = _solution("kv_decode")
    q = [0.25, -1.0, 0.5]
    k = [[1.0, 0.0, 0.5], [0.0, -1.0, 1.0], [0.25, 0.5, -0.75]]
    v = [[-1.0, 2.0], [4.0, -3.0], [0.5, 0.25]]
    shift = [2.5, -6.0]
    base = solution.kv_decode(q=list(q), k=copy.deepcopy(k), v=copy.deepcopy(v))
    shifted = solution.kv_decode(q=list(q), k=copy.deepcopy(k), v=_add_vector(v, shift))
    expected = [base[index] + shift[index] for index in range(len(base))]
    max_abs, max_rel = _assert_close(shifted, expected, "kv_decode value-shift invariance")
    return {"ok": True, "errors": [], "warnings": [], "details": {"max_abs_error": max_abs, "max_rel_error": max_rel}}


def _run_audit(name: str, audit: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        result = audit()
    except Exception as exc:  # pragma: no cover - exercised by CLI behavior.
        return {"name": name, "ok": False, "errors": [f"{type(exc).__name__}: {exc}"], "warnings": [], "details": {}}
    result["name"] = name
    return result


def run_public_audit() -> dict[str, Any]:
    audits: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("solution_static_boundary", _audit_static_boundary),
        ("rmsnorm_sign_symmetry", _audit_rmsnorm_sign_symmetry),
        ("rope_identity_and_pair_norm", _audit_rope_identity_and_norm),
        ("attention_value_shift_invariance", _audit_attention_value_shift),
        ("kv_decode_value_shift_invariance", _audit_kv_decode_value_shift),
    ]
    results = [_run_audit(name, audit) for name, audit in audits]
    return {
        "challenge": "limes-kernelforge",
        "ok": all(result["ok"] for result in results),
        "audit_count": len(results),
        "tolerance": {"abs": ABS_TOL, "rel": REL_TOL},
        "audits": results,
    }


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
