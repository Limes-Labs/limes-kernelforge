from __future__ import annotations

import copy
import importlib
import json
import math
from pathlib import Path
from typing import Any, Callable

from harness import reference
from harness.scoring import error_stats


ROOT = Path(__file__).resolve().parents[1]
ABS_TOL = 1e-9
REL_TOL = 1e-9


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _all_finite(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    if isinstance(value, (list, tuple)):
        return all(_all_finite(item) for item in value)
    return False


def _within_tolerance(actual: Any, expected: Any) -> None:
    max_abs, max_rel = error_stats(actual, expected)
    _assert(max_abs <= ABS_TOL, f"max_abs_error {max_abs} exceeds {ABS_TOL}")
    _assert(max_rel <= REL_TOL, f"max_rel_error {max_rel} exceeds {REL_TOL}")


def _solution(name: str):
    return importlib.import_module(f"solution.{name}")


def _probe_rmsnorm_finite_shape() -> dict[str, Any]:
    solution = _solution("rmsnorm")
    x = [[0.0, 0.0, 0.0, 0.0], [1_000_000.0, -1_000_000.0, 1e-9, -1e-9]]
    weight = [1.0, -0.5, 0.25, 2.0]
    actual = solution.rmsnorm(copy.deepcopy(x), list(weight), 1e-6)
    expected = reference.rmsnorm(copy.deepcopy(x), list(weight), 1e-6)
    _within_tolerance(actual, expected)
    _assert(len(actual) == len(x), "rmsnorm must preserve row count")
    _assert(all(len(row) == len(x[0]) for row in actual), "rmsnorm must preserve row width")
    _assert(_all_finite(actual), "rmsnorm output must be finite")
    return {"rows": len(actual), "dim": len(actual[0])}


def _probe_rope_does_not_mutate_inputs() -> dict[str, Any]:
    solution = _solution("rope")
    q = [[1.0, 2.0, -1.0, 0.5], [-0.25, 0.75, 1.5, -1.0]]
    k = [[0.5, -0.5, 2.0, 0.0], [1.0, 1.0, -0.75, 0.25]]
    cos = [[1.0, 0.0], [0.0, -1.0]]
    sin = [[0.0, 1.0], [1.0, 0.0]]
    before = copy.deepcopy((q, k, cos, sin))
    actual = solution.apply_rope(q, k, cos, sin)
    expected = reference.apply_rope(*copy.deepcopy(before))
    _within_tolerance(actual, expected)
    _assert((q, k, cos, sin) == before, "apply_rope must not mutate inputs")
    return {"rows": len(q), "dim": len(q[0])}


def _probe_attention_prefix_invariance() -> dict[str, Any]:
    solution = _solution("attention")
    q = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
    k = [[1.0, 0.0], [0.0, 1.0], [2.0, 2.0]]
    v = [[3.0, -1.0], [5.0, 2.0], [7.0, 9.0]]
    changed_k = copy.deepcopy(k)
    changed_v = copy.deepcopy(v)
    changed_k[2] = [10_000.0, 10_000.0]
    changed_v[2] = [999_999.0, -999_999.0]
    base = solution.causal_attention_prefill(copy.deepcopy(q), copy.deepcopy(k), copy.deepcopy(v))
    changed = solution.causal_attention_prefill(copy.deepcopy(q), changed_k, changed_v)
    expected = reference.causal_attention_prefill(copy.deepcopy(q), copy.deepcopy(k), copy.deepcopy(v))
    _within_tolerance(base, expected)
    _within_tolerance(base[:2], changed[:2])
    _assert(_all_finite(base), "attention output must be finite")
    return {"prefix_rows_checked": 2}


def _probe_kv_decode_alias_equivalence() -> dict[str, Any]:
    solution = _solution("kv_decode")
    q = [0.5, -0.5]
    k = [[1.0, 0.0], [1.0, 0.0], [0.0, -1.0], [0.0, -1.0]]
    v = [[1.0, 0.0], [2.0, 0.5], [-1.0, 3.0], [-2.0, 4.0]]
    canonical = solution.kv_decode(q=list(q), k=copy.deepcopy(k), v=copy.deepcopy(v))
    aliases = solution.kv_decode(query=list(q), keys=copy.deepcopy(k), values=copy.deepcopy(v))
    expected = reference.kv_decode(q=list(q), k=copy.deepcopy(k), v=copy.deepcopy(v))
    _within_tolerance(canonical, expected)
    _within_tolerance(aliases, expected)
    _within_tolerance(canonical, aliases)
    _assert(_all_finite(canonical), "kv_decode output must be finite")
    return {"cache_length": len(k), "dim": len(q)}


def _run_probe(name: str, probe: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        details = probe()
    except Exception as exc:  # pragma: no cover - exercised by CLI behavior.
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "details": details}


def run_invariant_probes() -> dict[str, Any]:
    probes: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("rmsnorm_finite_shape", _probe_rmsnorm_finite_shape),
        ("rope_inputs_are_not_mutated", _probe_rope_does_not_mutate_inputs),
        ("attention_prefix_invariance", _probe_attention_prefix_invariance),
        ("kv_decode_alias_equivalence", _probe_kv_decode_alias_equivalence),
    ]
    results = [_run_probe(name, probe) for name, probe in probes]
    return {
        "challenge": "limes-kernelforge",
        "ok": all(result["ok"] for result in results),
        "probe_count": len(results),
        "probes": results,
    }


def dumps_report(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"
