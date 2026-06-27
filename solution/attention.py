from __future__ import annotations

import math


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _softmax(values: list[float]) -> list[float]:
    offset = max(values)
    exps = [math.exp(value - offset) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def causal_attention_prefill(
    q: list[list[float]],
    k: list[list[float]],
    v: list[list[float]]
) -> list[list[float]]:
    dim = len(q[0])
    scale = 1.0 / math.sqrt(dim)
    output: list[list[float]] = []
    for token_index, query in enumerate(q):
        logits = [_dot(query, key) * scale for key in k[: token_index + 1]]
        weights = _softmax(logits)
        row = [0.0 for _ in v[0]]
        for weight, value_row in zip(weights, v[: token_index + 1]):
            for index, value in enumerate(value_row):
                row[index] += weight * value
        output.append(row)
    return output
