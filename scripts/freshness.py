"""Source freshness and coverage rules for Institutional Signals.

No network I/O: source checks must be supplied by an ingestion adapter.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable


def as_utc(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("All timestamps must be timezone-aware")
    return timestamp.astimezone(timezone.utc)


def source_health(
    *,
    checked_at: datetime | None,
    now: datetime,
    target_minutes: int,
    consecutive_failures: int = 0,
    published_at: datetime | None = None,
) -> dict:
    """Rate a source's *check* freshness separately from document publication age.

    An old annual publication is not stale if the publisher was successfully
    checked recently and no new release is due.
    """
    current_time = as_utc(now)
    if target_minutes <= 0 or consecutive_failures < 0:
        raise ValueError("Invalid target or failure count")
    if checked_at is None:
        check_age_minutes = None
        status = "unavailable"
    else:
        elapsed = (current_time - as_utc(checked_at)).total_seconds() / 60
        if elapsed < 0:
            raise ValueError("Last successful check cannot be in the future")
        check_age_minutes = round(elapsed, 2)
        if consecutive_failures >= 3:
            status = "unavailable"
        elif elapsed <= 1.5 * target_minutes and consecutive_failures == 0:
            status = "current"
        elif elapsed <= 3.0 * target_minutes:
            status = "delayed"
        else:
            status = "stale"
    publication_age_minutes = None
    if published_at is not None:
        publication_age_minutes = round((current_time - as_utc(published_at)).total_seconds() / 60, 2)
        if publication_age_minutes < 0:
            raise ValueError("Publication time cannot be in the future")
    return {
        "status": status,
        "last_success_age_minutes": check_age_minutes,
        "publication_age_minutes": publication_age_minutes,
        "failed_attempts_since_success": consecutive_failures,
    }


def required_source_coverage(statuses: Iterable[str]) -> dict:
    """Evaluate required feeds. Never turn an outage into evidence of no event."""
    values = list(statuses)
    if not values:
        return {"fraction_current": 0.0, "safe_to_claim_current": False}
    if any(s not in {"current", "delayed", "stale", "unavailable"} for s in values):
        raise ValueError("Unknown source status")
    current = sum(s == "current" for s in values)
    return {
        "fraction_current": current / len(values),
        "safe_to_claim_current": current == len(values),
    }
