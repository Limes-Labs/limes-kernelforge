from __future__ import annotations

import math


def rmsnorm(x: list[list[float]], weight: list[float], eps: float = 1e-6) -> list[list[float]]:
    result: list[list[float]] = []
    for row in x:
        mean_square = sum(value * value for value in row) / len(row)
        scale = 1.0 / math.sqrt(mean_square + eps)
        result.append([value * scale * weight[index] for index, value in enumerate(row)])
    return result
