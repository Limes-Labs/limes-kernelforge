from __future__ import annotations

import math


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _softmax(values: list[float]) -> list[float]:
    offset = max(values)
    exps = [math.exp(value - offset) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def kv_decode(
    q: list[float] | None = None,
    k: list[list[float]] | None = None,
    v: list[list[float]] | None = None,
    query: list[float] | None = None,
    keys: list[list[float]] | None = None,
    values: list[list[float]] | None = None
) -> list[float]:
    if query is not None:
        q = query
    if keys is not None:
        k = keys
    if values is not None:
        v = values
    if q is None or k is None or v is None:
        raise ValueError("kv_decode requires q/k/v or query/keys/values")
    scale = 1.0 / math.sqrt(len(q))
    logits = [_dot(q, key) * scale for key in k]
    weights = _softmax(logits)
    row = [0.0 for _ in v[0]]
    for weight, value_row in zip(weights, v):
        for index, value in enumerate(value_row):
            row[index] += weight * value
    return row
