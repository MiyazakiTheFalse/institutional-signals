#!/usr/bin/env python3
"""Validate curated institutional records and export deterministic static JSON."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUT = ROOT / "public" / "data" / "dashboard.json"


def read_json(name: str) -> list[dict]:
    path = DATA / name
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, list):
        raise ValueError(f"{name} must contain a JSON array")
    return content


def require_date(value: str, field: str) -> None:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc


def require_utc(value: str, field: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, AttributeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}: {value!r}") from exc
    if timestamp.tzinfo is None:
        raise ValueError(f"{field} must contain timezone")
    return timestamp.astimezone(timezone.utc)


def validate_and_export() -> dict:
    from coverage import evaluate_cases
    from upload_requests import requests_for
    sources = read_json("source_registry.json")
    observations = read_json("observations.json")
    forecasts = read_json("forecasts.json")
    src_ids = set()
    for source in sources:
        for field in ("id", "title", "publisher", "url", "published_at", "verified_at", "type"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                raise ValueError(f"Source missing {field}: {source!r}")
        if source["id"] in src_ids:
            raise ValueError(f"Duplicate source id: {source['id']}")
        src_ids.add(source["id"])
        parsed = urlparse(source["url"])
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError(f"Source URL not HTTPS: {source['id']}")
        require_date(source["published_at"], "published_at")
        require_date(source["verified_at"], "verified_at")

    observation_ids = set()
    for row in observations:
        for field in ("id", "date", "summary", "subject", "event_type", "status"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"Observation missing {field}: {row!r}")
        if row["id"] in observation_ids:
            raise ValueError(f"Duplicate observation id: {row['id']}")
        observation_ids.add(row["id"])
        require_date(row["date"], "observation.date")
        references = row.get("source_ids")
        if not isinstance(references, list) or not references or not set(references).issubset(src_ids):
            raise ValueError(f"Observation source references invalid: {row['id']}")

    forecast_ids = set()
    for row in forecasts:
        required = ("id", "question", "institution", "created_at", "close_at", "resolve_by", "resolution_rule", "status", "evidence_source_ids")
        if any(field not in row for field in required):
            raise ValueError(f"Forecast lacks required fields: {row!r}")
        if row["id"] in forecast_ids:
            raise ValueError(f"Duplicate forecast id: {row['id']}")
        forecast_ids.add(row["id"])
        created = require_utc(row["created_at"], "created_at")
        close = require_utc(row["close_at"], "close_at")
        resolved = require_utc(row["resolve_by"], "resolve_by")
        if not created < close <= resolved:
            raise ValueError(f"Invalid forecast ordering: {row['id']}")
        prob = row.get("probability")
        if prob is not None and (type(prob) not in (int, float) or not 0 <= prob <= 1):
            raise ValueError(f"Invalid probability: {row['id']}")
        if row["status"] not in ("draft", "locked", "resolved", "unresolved"):
            raise ValueError(f"Invalid forecast status: {row['id']}")
        if row["status"] != "draft" and prob is None:
            raise ValueError(f"Non-draft forecast must have probability: {row['id']}")
        refs = row["evidence_source_ids"]
        if not isinstance(refs, list) or not set(refs).issubset(src_ids):
            raise ValueError(f"Forecast references invalid: {row['id']}")
        if row["status"] == "resolved":
            if type(row.get("outcome")) is not bool:
                raise ValueError(f"Resolved forecast needs binary outcome: {row['id']}")
            outcome_refs = row.get("outcome_source_ids", [])
            if not isinstance(outcome_refs, list) or not outcome_refs or not set(outcome_refs).issubset(src_ids):
                raise ValueError(f"Resolved forecast needs valid outcome references: {row['id']}")

    cases = json.loads((ROOT / 'config/case_dependencies.json').read_text(encoding='utf-8'))
    collection_sources = json.loads((ROOT / 'config/collection.json').read_text(encoding='utf-8'))
    reviewed = read_json('reviewed_evidence.json')
    # Static export never claims to know live R2 check state.
    gates = evaluate_cases(cases, collection_sources, {}, reviewed, datetime(2026, 11, 15, tzinfo=timezone.utc))
    return {
        "project": "Institutional Signals",
        "dataset_version": "0.1",
        "as_of": "2026-11-15",
        "notice": "Curated public-source research data; hypotheses are not findings of corruption. No forecast performance is claimed.",
        "sources": sorted(sources, key=lambda s: (s["published_at"], s["id"]), reverse=True),
        "observations": sorted(observations, key=lambda r: (r["date"], r["id"]), reverse=True),
        "forecasts": sorted(forecasts, key=lambda r: r["created_at"], reverse=True),
        "upload_requests": requests_for(cases, gates),
        "readiness_mode": "static_requirements_only_not_live_coverage",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if static output is not in sync")
    args = parser.parse_args()
    try:
        data = validate_and_export()
        formatted = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != formatted:
                raise ValueError("Generated dashboard.json out of sync; run python scripts/build_data.py")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_text(formatted, encoding="utf-8")
        print(f"Validated {len(data['sources'])} sources, {len(data['observations'])} observations, {len(data['forecasts'])} forecasts")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
