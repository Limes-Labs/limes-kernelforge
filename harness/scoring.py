"""Scoring helpers for the public smoke harness."""

import importlib
import math
import platform
import statistics
import time

from harness import reference


TASKS = {
    "rmsnorm": {
        "solution_module": "solution.rmsnorm",
        "solution_func": "rmsnorm",
        "reference_func": reference.rmsnorm,
    },
    "rope": {
        "solution_module": "solution.rope",
        "solution_func": "apply_rope",
        "reference_func": reference.apply_rope,
    },
    "causal_attention_prefill": {
        "solution_module": "solution.attention",
        "solution_func": "causal_attention_prefill",
        "reference_func": reference.causal_attention_prefill,
    },
    "kv_decode_microcase": {
        "solution_module": "solution.kv_decode",
        "solution_func": "kv_decode",
        "reference_func": reference.kv_decode,
    },
}


def flatten_numbers(value):
    if isinstance(value, (int, float)):
        return [float(value)]
    if isinstance(value, (list, tuple)):
        out = []
        for item in value:
            out.extend(flatten_numbers(item))
        return out
    raise TypeError(f"unsupported output value: {type(value)!r}")


def error_stats(actual, expected):
    actual_values = flatten_numbers(actual)
    expected_values = flatten_numbers(expected)
    if len(actual_values) != len(expected_values):
        raise AssertionError(
            f"output length mismatch: {len(actual_values)} != {len(expected_values)}"
        )
    max_abs = 0.0
    max_rel = 0.0
    for got, want in zip(actual_values, expected_values):
        abs_error = abs(got - want)
        rel_error = abs_error / max(abs(want), 1e-12)
        max_abs = max(max_abs, abs_error)
        max_rel = max(max_rel, rel_error)
    return max_abs, max_rel


def geomean(values):
    positives = [max(value, 1e-12) for value in values]
    return math.exp(sum(math.log(value) for value in positives) / len(positives))


def hardware_fingerprint():
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def load_solution(task_name):
    task = TASKS[task_name]
    module = importlib.import_module(task["solution_module"])
    return getattr(module, task["solution_func"])


def run_case(task_name, case, repeats=9, abs_tol=1e-9, rel_tol=1e-9):
    task = TASKS[task_name]
    inputs = case["inputs"]
    expected = task["reference_func"](**inputs)
    candidate = load_solution(task_name)
    actual = candidate(**inputs)
    max_abs, max_rel = error_stats(actual, expected)
    correct = max_abs <= abs_tol or max_rel <= rel_tol

    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        candidate(**inputs)
        timings.append((time.perf_counter() - start) * 1000.0)

    return {
        "task": task_name,
        "case": case["name"],
        "correct": correct,
        "max_abs_error": max_abs,
        "max_rel_error": max_rel,
        "runtime_ms": statistics.median(timings),
    }


def score_cases(cases_payload, repeats=9):
    results = []
    for task_name, cases in cases_payload["tasks"].items():
        if task_name not in TASKS:
            raise KeyError(f"unknown task in cases: {task_name}")
        for case in cases:
            results.append(run_case(task_name, case, repeats=repeats))

    max_abs = max(result["max_abs_error"] for result in results)
    max_rel = max(result["max_rel_error"] for result in results)
    runtimes = [result["runtime_ms"] for result in results]
    return {
        "correct": all(result["correct"] for result in results),
        "max_abs_error": max_abs,
        "max_rel_error": max_rel,
        "public_geomean_runtime_ms": geomean(runtimes),
        "backend": "python-stdlib",
        "hardware_fingerprint": hardware_fingerprint(),
        "cases": results,
    }

