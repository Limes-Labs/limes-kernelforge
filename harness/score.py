#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import json
import math
import platform
import statistics
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import reference
from harness.scoring import score_cases


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_CASES = ROOT / "cases" / "public_smoke" / "cases.json"
PUBLIC_STRESS_CASES = ROOT / "cases" / "public_smoke" / "stress_cases.json"
ABS_TOL = 1e-9
REL_TOL = 1e-9


def _load_cases() -> dict[str, Any]:
    return json.loads(PUBLIC_CASES.read_text(encoding="utf-8"))


def _load_stress_cases() -> dict[str, Any]:
    return json.loads(PUBLIC_STRESS_CASES.read_text(encoding="utf-8"))


def _flatten(value: Any) -> list[float]:
    if isinstance(value, list):
        flattened: list[float] = []
        for item in value:
            flattened.extend(_flatten(item))
        return flattened
    return [float(value)]


def _error(expected: Any, actual: Any) -> tuple[float, float]:
    expected_values = _flatten(expected)
    actual_values = _flatten(actual)
    if len(expected_values) != len(actual_values):
        return float("inf"), float("inf")
    max_abs = 0.0
    max_rel = 0.0
    for exp, act in zip(expected_values, actual_values):
        abs_error = abs(exp - act)
        rel_error = abs_error / max(1e-12, abs(exp))
        max_abs = max(max_abs, abs_error)
        max_rel = max(max_rel, rel_error)
    return max_abs, max_rel


def _median_ms(function, *args) -> float:
    for _ in range(2):
        function(*args)
    timings: list[float] = []
    for _ in range(5):
        start = time.perf_counter()
        function(*args)
        timings.append((time.perf_counter() - start) * 1000.0)
    return statistics.median(timings)


def _run_primitive(name: str, expected_function, solution_function, args: tuple[Any, ...]) -> dict[str, Any]:
    expected = expected_function(*args)
    actual = solution_function(*args)
    max_abs, max_rel = _error(expected, actual)
    reference_runtime_ms = _median_ms(expected_function, *args)
    runtime_ms = _median_ms(solution_function, *args)
    speedup = reference_runtime_ms / max(runtime_ms, 1e-12)
    return {
        "max_abs_error": max_abs,
        "max_rel_error": max_rel,
        "runtime_ms": runtime_ms,
        "reference_runtime_ms": reference_runtime_ms,
        "runtime_delta_ms": runtime_ms - reference_runtime_ms,
        "speedup_vs_reference": speedup,
        "correct": max_abs <= ABS_TOL and max_rel <= REL_TOL
    }


def public_score() -> dict[str, Any]:
    cases = _load_cases()
    stress = score_cases(_load_stress_cases(), repeats=1)
    solution_rmsnorm = importlib.import_module("solution.rmsnorm")
    solution_rope = importlib.import_module("solution.rope")
    solution_attention = importlib.import_module("solution.attention")
    solution_kv_decode = importlib.import_module("solution.kv_decode")

    primitive_results = {
        "rmsnorm": _run_primitive(
            "rmsnorm",
            reference.rmsnorm,
            solution_rmsnorm.rmsnorm,
            (cases["rmsnorm"]["x"], cases["rmsnorm"]["weight"], cases["rmsnorm"]["eps"]),
        ),
        "rope": _run_primitive(
            "rope",
            reference.rope,
            solution_rope.rope,
            (cases["rope"]["x"], cases["rope"]["positions"], cases["rope"]["theta"]),
        ),
        "attention": _run_primitive(
            "attention",
            reference.causal_attention_prefill,
            solution_attention.causal_attention_prefill,
            (cases["attention"]["q"], cases["attention"]["k"], cases["attention"]["v"]),
        ),
        "kv_decode": _run_primitive(
            "kv_decode",
            reference.kv_decode,
            solution_kv_decode.kv_decode,
            (cases["kv_decode"]["q"], cases["kv_decode"]["k"], cases["kv_decode"]["v"]),
        ),
    }
    runtimes = [max(1e-12, item["runtime_ms"]) for item in primitive_results.values()]
    reference_runtimes = [
        max(1e-12, item["reference_runtime_ms"])
        for item in primitive_results.values()
    ]
    geomean = math.exp(sum(math.log(value) for value in runtimes) / len(runtimes))
    reference_geomean = math.exp(
        sum(math.log(value) for value in reference_runtimes) / len(reference_runtimes)
    )
    primary_correct = all(item["correct"] for item in primitive_results.values())
    primary_max_abs = max(item["max_abs_error"] for item in primitive_results.values())
    primary_max_rel = max(item["max_rel_error"] for item in primitive_results.values())
    return {
        "correct": primary_correct and stress["correct"],
        "primary_correct": primary_correct,
        "max_abs_error": max(primary_max_abs, stress["max_abs_error"]),
        "max_rel_error": max(primary_max_rel, stress["max_rel_error"]),
        "public_geomean_runtime_ms": geomean,
        "reference_public_geomean_runtime_ms": reference_geomean,
        "public_runtime_delta_ms": geomean - reference_geomean,
        "public_speedup_vs_reference": reference_geomean / max(geomean, 1e-12),
        "public_stress_correct": stress["correct"],
        "public_stress_case_count": len(stress["cases"]),
        "public_stress_max_abs_error": stress["max_abs_error"],
        "public_stress_max_rel_error": stress["max_rel_error"],
        "public_stress_geomean_runtime_ms": stress["public_geomean_runtime_ms"],
        "reference_public_stress_geomean_runtime_ms": stress["reference_public_geomean_runtime_ms"],
        "public_stress_speedup_vs_reference": stress["public_speedup_vs_reference"],
        "backend": "python-stdlib",
        "tolerance": {
            "abs": ABS_TOL,
            "rel": REL_TOL
        },
        "hardware_fingerprint": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "python": platform.python_version()
        },
        "primitives": primitive_results
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Limes KernelForge public smoke scorer.")
    parser.add_argument("--output", default="score.json")
    args = parser.parse_args()
    result = public_score()
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["correct"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
