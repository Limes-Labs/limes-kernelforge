from __future__ import annotations

import math


def rope(x: list[list[float]], positions: list[int], theta: float = 10000.0) -> list[list[float]]:
    if not x:
        return []
    dim = len(x[0])
    if dim % 2 != 0:
        raise ValueError("RoPE expects an even dimension")
    output: list[list[float]] = []
    for row, position in zip(x, positions):
        rotated = [0.0] * dim
        for pair in range(dim // 2):
            angle = position / (theta ** (2 * pair / dim))
            cos_v = math.cos(angle)
            sin_v = math.sin(angle)
            first = row[2 * pair]
            second = row[2 * pair + 1]
            rotated[2 * pair] = first * cos_v - second * sin_v
            rotated[2 * pair + 1] = first * sin_v + second * cos_v
        output.append(rotated)
    return output


def _apply_rope_one(
    x: list[list[float]],
    cos: list[list[float]],
    sin: list[list[float]]
) -> list[list[float]]:
    output: list[list[float]] = []
    for row, cos_row, sin_row in zip(x, cos, sin):
        rotated = [0.0] * len(row)
        for pair, (cos_v, sin_v) in enumerate(zip(cos_row, sin_row)):
            first = row[2 * pair]
            second = row[2 * pair + 1]
            rotated[2 * pair] = first * cos_v - second * sin_v
            rotated[2 * pair + 1] = first * sin_v + second * cos_v
        output.append(rotated)
    return output


def apply_rope(
    q: list[list[float]],
    k: list[list[float]],
    cos: list[list[float]],
    sin: list[list[float]]
) -> list[list[list[float]]]:
    return [_apply_rope_one(q, cos, sin), _apply_rope_one(k, cos, sin)]
