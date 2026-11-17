# Verified evidence to experimental forecast — implementation slice

Implements architecture v0.2's first batch inference boundary without claiming deployment or a trained model.

## Files
- `scripts/evidence_journal.py`: create content-addressed events from *human-verified* review records, append-only disk writer, correction and historical as-of replay.
- `scripts/forecast_pipeline.py`: apply existing `coverage.evaluate` dependency gate, deduplicate underlying primary documents, compare verified evidence fingerprints, issue baseline snapshots with the existing `forecast_engine`.
- `tests/test_evidence_pipeline.py`: no changes, outage, correction, de-duplication, temporal exclusion, sparse labels, immutability.

## Running the batch tool
Use explicit reviewed inputs, not raw collector changes. The existing repository has no activated production cases or adequate resolved labels, and intentionally contains empty `config/forecast_cases.json` and `data/resolved_outcomes.json`.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/forecast_pipeline.py \
  --case /path/to/case.json \
  --requirements /path/to/requirements.json \
  --sources /path/to/sources.json \
  --state /path/to/historically-correct-source-state.json \
  --reviews /path/to/verified-reviews.json \
  --journal /path/to/immutable-event-journal \
  --outcomes /path/to/resolved-outcomes.json \
  --as-of 2026-11-17T12:00:00Z \
  --output /path/to/immutable-forecasts
```

The case uses existing `forecast_engine.baseline_snapshot` fields: `case_id`, `question`, `resolution_rule`, `model_version`, `horizon_end`. Requirements use `config/case_dependencies.json`'s `requirements` **array for the selected case**, not the surrounding case object. Source state must be reconstructible as of the forecast's timestamp. A forecast is held unless essential requirements are current/verified and enough independent resolved outcomes exist.

`event_from_review(...)` requires a verified review record and explicit `event_type`/`institution_ids`; it does not perform extraction or automated trust decisions. Give every reviewed source a stable `primary_document_id`. Corrections use `supersedes` and produce a new immutable event. Calling `issue(...,previous=snapshot)` avoids reissuing on unchanged verified evidence. The CLI is a one-shot first-run interface and does not itself load prior snapshots.

## Remaining work before activation
- Connect existing R2 reviewed/manual records and collector status to a durable per-case processing queue, idempotent retries, real as-of source-state versions, and atomic R2 writes.
- Add explicit supervised extraction and independent validation; a scanned document alone is not a verified claim.
- Implement real D1 metadata, Worker cron, health monitoring and reconciliation; the existing collector is distinct.
- Populate case registries and independently resolved outcome labels; evaluate calibration and out-of-time generalisation before public probabilities.
- Integrate forecast audits into the desktop UI. No new model parameters, retraining, Cloudflare deployment, or public forecast is activated by this change.

No inference can establish non-public decisions, unlawful conduct or missing events from a source outage.
