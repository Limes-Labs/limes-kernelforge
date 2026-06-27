from __future__ import annotations

import math


Vector = list[float]
Matrix = list[Vector]


def rmsnorm(x: Matrix, weight: Vector, eps: float = 1e-6) -> Matrix:
    result: Matrix = []
    for row in x:
        mean_square = sum(value * value for value in row) / len(row)
        scale = 1.0 / math.sqrt(mean_square + eps)
        result.append([value * scale * weight[index] for index, value in enumerate(row)])
    return result


def rope(x: Matrix, positions: list[int], theta: float = 10000.0) -> Matrix:
    if not x:
        return []
    dim = len(x[0])
    if dim % 2 != 0:
        raise ValueError("RoPE public reference expects an even dimension")
    output: Matrix = []
    half = dim // 2
    for row, position in zip(x, positions):
        rotated = [0.0] * dim
        for pair in range(half):
            angle = position / (theta ** (2 * pair / dim))
            cos_v = math.cos(angle)
            sin_v = math.sin(angle)
            first = row[2 * pair]
            second = row[2 * pair + 1]
            rotated[2 * pair] = first * cos_v - second * sin_v
            rotated[2 * pair + 1] = first * sin_v + second * cos_v
        output.append(rotated)
    return output


def _apply_rope_one(x: Matrix, cos: Matrix, sin: Matrix) -> Matrix:
    output: Matrix = []
    for row, cos_row, sin_row in zip(x, cos, sin):
        rotated = [0.0] * len(row)
        for pair, (cos_v, sin_v) in enumerate(zip(cos_row, sin_row)):
            first = row[2 * pair]
            second = row[2 * pair + 1]
            rotated[2 * pair] = first * cos_v - second * sin_v
            rotated[2 * pair + 1] = first * sin_v + second * cos_v
        output.append(rotated)
    return output


def apply_rope(q: Matrix, k: Matrix, cos: Matrix, sin: Matrix) -> list[Matrix]:
    return [_apply_rope_one(q, cos, sin), _apply_rope_one(k, cos, sin)]


def _softmax(values: Vector) -> Vector:
    offset = max(values)
    exps = [math.exp(value - offset) for value in values]
    total = sum(exps)
    return [value / total for value in exps]


def _dot(left: Vector, right: Vector) -> float:
    return sum(a * b for a, b in zip(left, right))


def causal_attention_prefill(q: Matrix, k: Matrix, v: Matrix) -> Matrix:
    dim = len(q[0])
    scale = 1.0 / math.sqrt(dim)
    output: Matrix = []
    for token_index, query in enumerate(q):
        logits = [_dot(query, key) * scale for key in k[: token_index + 1]]
        weights = _softmax(logits)
        row = [0.0 for _ in v[0]]
        for weight, value_row in zip(weights, v[: token_index + 1]):
            for index, value in enumerate(value_row):
                row[index] += weight * value
        output.append(row)
    return output


def kv_decode(
    q: Vector | None = None,
    k: Matrix | None = None,
    v: Matrix | None = None,
    query: Vector | None = None,
    keys: Matrix | None = None,
    values: Matrix | None = None
) -> Vector:
    if query is not None:
        q = query
    if keys is not None:
        k = keys
    if values is not None:
        v = values
    if q is None or k is None or v is None:
        raise ValueError("kv_decode requires q/k/v or query/keys/values")
    dim = len(q)
    scale = 1.0 / math.sqrt(dim)
    logits = [_dot(q, key) * scale for key in k]
    weights = _softmax(logits)
    row = [0.0 for _ in v[0]]
    for weight, value_row in zip(weights, v):
        for index, value in enumerate(value_row):
            row[index] += weight * value
    return row
