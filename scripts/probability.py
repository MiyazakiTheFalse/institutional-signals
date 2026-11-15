"""Auditable baseline probability calculations; not a trained model."""
from __future__ import annotations

from math import prod
from typing import Iterable


def horizon_event_probability(hazards: Iterable[float]) -> float:
    """P(at least one event in horizon) for sequential conditional hazards."""
    values = list(hazards)
    if not values or any(not 0 <= h <= 1 for h in values):
        raise ValueError("Supply one or more hazards between 0 and 1")
    return 1.0 - prod(1.0 - h for h in values)


def beta_binomial_base_rate(*, events: int, observations: int, alpha: float = 1.0, beta: float = 1.0) -> float:
    """A smoothed event-rate baseline; relies on exchangeable Bernoulli trials."""
    if not 0 <= events <= observations or alpha <= 0 or beta <= 0:
        raise ValueError("Invalid counts or Beta prior")
    return (events + alpha) / (observations + alpha + beta)


def brier_score(predictions: Iterable[tuple[float, int]]) -> float:
    """Mean squared error for *resolved* binary probability forecasts."""
    pairs = list(predictions)
    if not pairs or any(not (0 <= p <= 1 and y in (0, 1)) for p, y in pairs):
        raise ValueError("Supply resolved (probability, binary outcome) pairs")
    return sum((p - y) ** 2 for p, y in pairs) / len(pairs)
