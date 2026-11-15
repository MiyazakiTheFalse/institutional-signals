# Research MVP design

## Purpose

Collect public evidence, track institutional decisions, and assess predictions against explicit resolution criteria. Anomalies are investigation leads, not proof of corruption.

## First case

Thames Water / Ofwat. Source families to verify before ingestion: Ofwat publications, UK Parliament records, Companies House filings and original company disclosures.

## Pipeline

1. Fetch permitted public records on a daily GitHub Actions schedule, respecting source terms, rate limits and access restrictions.
2. Retain source URL, publication date, retrieval timestamp, content hash and parser version with each snapshot.
3. Normalize documents into institution, event and evidence records; deduplicate by stable source ID and hash.
4. Validate required fields, dates and provenance. Quarantine invalid records and report source failures explicitly.
5. Publish versioned JSON for the dashboard; retain larger snapshots as compressed artifacts with a defined retention policy.

## Predictions

Record a unique ID, creation timestamp, precise claim, deadline, probability, evidence links, baseline and resolution criteria before the outcome. Preserve revisions as separate timestamped versions with reasons. Resolve outcomes using linked evidence; mark ambiguous cases unresolved. Measure calibration and Brier scores on resolved forecasts and compare against simple baselines. Avoid training on information published after the forecast.

## Delivery sequence

- Verify source URLs, licensing, available feeds and access requirements.
- Implement one source adapter with fixture-based parsing checks.
- Add validation and scheduled ingestion with failure reporting.
- Build the evidence timeline and prediction register.
- Add the React dashboard and configure Cloudflare deployment.
- Evaluate forecasts before adding statistical models.

## Cost controls

Start with small JSON datasets, bounded collection windows and cached HTTP requests. Track GitHub Actions and hosting usage against applicable allowances before enabling schedules. Free-tier availability is not guaranteed.
