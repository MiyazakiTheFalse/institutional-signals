# Institutional Signals — Continuous Freshness & Probabilistic ML Architecture

**Status:** Technical design specification, not a deployed service  
**Version:** 0.2 draft | **Date:** 2026-11-15  
**Scope:** Every institution, case, source, monitored outcome, and user forecasting task.

## 1. Non-negotiable design goals

1. Collect source updates continuously through scheduled polling or official webhooks, subject to source availability, legal and technical constraints.
2. Represent *actual observed freshness*, never imply that a private/unpublished decision is known.
3. Distinguish `source_publication_time`, `source_updated_time`, `retrieved_at`, `ingested_at`, `validated_at`, `forecast_as_of`, and `model_trained_at`, all in UTC.
4. Immutable record of raw evidence and previously issued predictions, including their model and feature versions.
5. Recompute forecasts when material **verified evidence** changes; retrain the underlying model only after enough labelled outcomes exist.
6. Never treat retrieval failures or a lack of new announcements as evidence that an event did not happen.
7. All historical evaluations reconstruct information **available at the forecast time** to avoid look-ahead leakage.
8. Apply the same source-quality and forecasting contract to every institution and case.
9. Abstain, qualify, or flag forecasts when vital data is too old or coverage is incomplete.
10. Optimize operating costs toward £0 per month for a small public MVP, acknowledging free-tier limits and lack of a hard service-level guarantee.

## 2. What 'always up to date' can mean

**External truth is not the same as observable data.** No system can know an event before an institution publishes it or another lawful, reliable source reports it. Our operational promise is *continuous checks + bounded, monitored detection delay for selected sources*, not omniscience or 100% uptime.

Freshness dimensions:
- **Poll freshness:** time since last successful verification that a source was queried.
- **Publication freshness:** time since latest published source data. This may legitimately be months for an annual report.
- **Processing freshness:** time since newly observed source data became structured, verified evidence.
- **Forecast freshness:** time since the latest material evidence was incorporated into an issued forecast.
- **Model freshness:** version of parameters and training cutoff; not necessarily a problem if new information is handled through inference rather than parameter retraining.
- **Coverage:** fraction of required sources queried successfully within their target periods.

### Proposed MVP service targets (aspirational, not guaranteed)

| Source class | Normal checking target | Processing target after detection | Initial priority |
|---|---:|---:|---|
| Official, time-sensitive releases | 5–15 min | 5 min | Critical |
| Regulators, government, public statements | 30–60 min | 10 min | High |
| Corporate filings | 30–60 min, respecting API limits | 10 min | High |
| Periodic statistical tables | Daily / publication-calendar aligned | 24 h | Medium |
| Corrections and reconciliation | Daily | 24 h | Medium |

Configured per source. When the check is late (>1.5× target) mark `delayed`; very late (>3× target) or repeated errors mark `stale/unavailable`. Check freshness independently from source publication age. Missing coverage can suspend claims of currentness.

## 3. Per-case universal data contract

Every case: `case_id`, `sector_id`, `institution_ids`, `jurisdiction`, `forecast_question`, `outcome_definition`, `forecast_horizon`, `eligibility_rules`, `source_ids`, `feature_config_version`, `evaluation_policy`.

Every source: `source_id`, `institution_id`, `type`, `publisher`, `canonical_url`, `api_url`, `license`, `robots_terms`, `poll_target_minutes`, `expected_publication_pattern`, `priority`, `etag`, `last_modified`, `last_attempt_at`, `last_success_at`, `latest_publication_at`, `coverage_state`, `consecutive_failures`, `backoff_until`, `revision_policy`.

Every evidence event: `event_id`, `source_id`, `canonical_document_id`, `content_hash_sha256`, `published_at`, `source_updated_at`, `observed_at`, `fetched_at`, `verified_at`, `event_type`, `institution_ids`, `structured_claims`, `quality`, `duplicate_group`, `raw_blob_ref`, `parser_version`, `human_review_state`.

Every forecast: `forecast_id`, `case_id`, `question_version`, `issued_at`, `as_of`, `horizon_end`, `p_event`, `status`, `source_coverage`, `feature_snapshot_hash`, `evidence_ids`, `model_version`, `calibration_version`, `prior_forecast_id`, `change_reason`, `resolved_at`, `actual_outcome`, `scored_at`.

Public predictions append snapshots: never update a previous probability in place. Correct misinformation using a new evidence revision record referencing its predecessor.

## 4. Runtime pipeline

```text
Official feeds / APIs / publication sites / authorized webhooks
     |    schedule or push; conditional requests (ETag / Last-Modified)
     v
Lightweight change monitor (Cloudflare Worker Cron; UTC)
     |    source status; content hash; retry; rate limit; outage alert
     v
D1 metadata + immutable raw snapshots (R2 when enabled)
     |    event detection / dedup / extraction / validation
     v
Event journal + source dependency graph
     |    recompute only affected case features
     v
Forecast inference (existing model & calibration version)
     |    immutable forecast snapshots; explanations and as-of times
     v
Dashboard/API + notifications + reliability/coverage status

Separately: batch Python jobs (GitHub Actions) perform heavy extraction,
backtesting, calibration and proposed model retraining. A scheduled reconciliation
pass checks missed publications and source corrections.
```

**Reliability controls:** health-heartbeat, missed-schedule watchdog, idempotent jobs, `If-None-Match` conditional requests, bounded exponential backoff with jitter, circuit-breakers, durable queue / reprocessing log, request timeout, 429 handling, publisher-specified rate limits, and per-source policy registry. Workers Free has very limited CPU per invocation; heavy text parsing and ML should run in Python jobs, not the short Worker tick. GitHub scheduled runs can be late or dropped, so Cron + reconciliation + alerts are essential, but still do not deliver a hard uptime guarantee.

**Storage:** D1 stores source and prediction metadata; R2 Standard can hold raw immutable snapshots and Parquet datasets where its free tier / account requirements permit. GitHub Actions build artifacts are not a permanent historical evidence store because they expire. Sensitive secrets must be set in platform secret stores; none in Git.

## 5. Mathematical forecast engine

### 5.1 Explicitly define the event and risk set

For non-recurrent event type `e` in institution `i`, define a discrete time hazard:

\[
h_{i,t,e} = P(Y_{i,t,e}=1 \mid Y_{i,<t,e}=0, \; X_{i,t}^{\text{as-of}}, \;g_i).
\]

A transparent first model is regularized pooled logistic regression, with elapsed time and sector intercepts. For a richer hierarchical variant:

\[
\operatorname{logit} h_{i,t,e}= \alpha_e + u_{g_i,e} + v_{i,e} + f_e(t) + \boldsymbol{\beta}_e^{\top} X_{i,t}^{\text{as-of}},
\]

where sector effects and institution effects use partial-pooling priors such as `u ~ Normal(0, sigma_sector)`, `v ~ Normal(0, sigma_institution)`. Avoid institution-specific high-capacity models with few event outcomes.

The probability of at least one event within horizon `H` follows:

\[
P(T_i\leq H)=1-\prod_{t=1}^{H}(1-h_{i,t,e}).
\]

Use repeated-event extensions (recurrent-event models) for actions that can happen multiple times, not a single-failure model.

### 5.2 Dynamic latent state where data justify it

Represent slowly changing institution pressure by a latent state:

\[
z_{i,t}=A z_{i,t-1}+\eta_{i,t}, \quad \eta_{i,t}\sim\mathcal N(0,Q).
\]

Observations update state and event hazard. Use a Kalman filter for approximately Gaussian indicators; particle/variational or other suitable Bayesian filtering for nonlinear categorical events. Differentiate **filter updates after new data** from **training a new parameter model**.

### 5.3 Change-point detection, not indiscriminate retraining

Monitor residuals, observed covariate distributions and publication-behaviour shifts with ADWIN or Bayesian online change-point detection. A drift alert triggers investigation and a candidate re-fit; it must not silently overwrite deployed models or assume misconduct.

### 5.4 Correlated evidence and source quality

Identical claims repeated by multiple outlets must be grouped by underlying primary source. Otherwise naive Bayesian multiplication would treat repetition as independent confirmation and produce overconfident predictions. Each source has provenance, publication latency, revisions and reliability metadata. Unknown publisher reliability should be measured, not invented.

### 5.5 Calibration and uncertainty

Record Brier score for resolved binary forecasts:

\[
\mathrm{BS}=\frac1N\sum_{j=1}^N(p_j-y_j)^2.
\]

Compare against sector base rates and simple no-change forecasts. Also compute log loss, reliability curves, calibration-in-the-large, event-specific coverage and forecast usefulness by lead time. Use Platt / isotonic calibration only where enough independent data exist. Adaptive conformal methods may be useful for time-series intervals when temporal dependence is important; their guarantees depend on the chosen method and conditions, and they do **not** magically make sparse binary-event probabilities calibrated.

**Uncertainty policy:** publish an interval or diagnostic uncertainty measure for sufficiently validated models; otherwise show `experimental / insufficient outcomes` rather than a fake precise 'confidence score'.

### 5.6 Concept drift and retraining decision

Every new material verified event => rebuild affected features and issue updated forecast with the current model (subject to freshness and quality checks).

Every newly *resolved target* => update the calibration / scoring ledger. Refit a candidate when enough new independent labels or meaningful drift warrants it, then promote only if rolling out-of-time evaluation shows improvement and no unacceptable degradation in critical segments. If there are only a handful of resolved cases, use conservative baselines and report insufficient evidence. Do not retrain blindly every hour.

### 5.7 Temporal validity / leakage prevention

Construct features only from documents known **as of** the forecast issuance time (`available_at <= forecast_as_of`), not their eventual corrected values or the retrospective publication metadata. For each backtest, replay the event journal in historical order. Use expanding-window walk-forward validation with appropriate gaps/embargoes; group correlated institutions or repeated events to avoid data contamination. Evaluate at event time and discovery time when delayed publication matters.

## 6. Continuous improvement policy

**On each source tick:** check, record success/failure, detect changes, store immutable evidence, parse and validate, update affected cases, create forecast snapshot as appropriate.

**Daily:** reconcile feeds and late/corrected documents, recompute freshness and coverage, detect errors; send source-outage alerts if configured.

**Weekly:** score newly resolved forecasts, compare current forecast performance with baselines and inspect drift diagnostics.

**Monthly / outcome-triggered:** train *candidate* models when enough independent observations exist; reproducible backtests; promote only with documented acceptance criteria and a rollback plan.

**Quarterly:** review source coverage, fairness across institution sectors, selection effects, data quality, and whether forecast targets remain substantively meaningful.

This system improves when verifiable outcomes accumulate; mere passage of time is not evidence that prediction skill improved.

## 7. Optimising the monitoring budget

Allocate source checks using estimated information value instead of polling every source every minute. For source `s`, an operational priority heuristic is:

\[
priority_s = \frac{w_s\,q_s\,r_s}{c_s},
\]

where `w` is expected materiality to live cases, `q` is estimated likelihood of a new release over the next interval, `r` is source reliability / relevance and `c` is monitoring cost. This is a *scheduling heuristic*, not an empirically validated predictive formula. Impose minimum polling for every required source, publication-calendar overrides, deadline escalation, and source-specific rate-limit caps.

## 8. Public-facing audit / ethics policy

A probability of regulatory enforcement or restructuring is a forecast of a defined **event**, not a statement about corruption or hidden personal motives. The public-facing application must show citations, forecast as-of timestamp, coverage and freshness, historical accuracy, counter-evidence, and a corrections path. No automated misconduct allegation should be inferred from an anomaly.

## 9. Suggested MVP implementation order

1. Source registry + typed case registry + event and prediction schema; tests enforcing UTC timestamps and immutable forecast IDs.
2. Polling pipeline with conditional HTTP requests, deduplication, retries, source health, reconciliation.
3. Historical 'as-of' event reconstruction; a source audit UI with stale badges and last-successful timestamps.
4. Basic sector base-rate model + pooled logistic / discrete hazard forecast; event-ledger scoring.
5. Incremental inference on material new evidence, immutable probability snapshots and change explanations.
6. Rolling prospective evaluation; only then hierarchical Bayes, state space, drift methods, advanced conformal diagnostics.
7. Multi-sector expansion, user-specific watchlists, and infrastructure scaling after reliability benchmarks.

### Acceptance tests

- Simulate no changes: collector records healthy check but no new forecast (unless horizon/time advancement requires it).
- Simulate release: new record is ingested exactly once, affected forecast reissued, old forecast preserved.
- Simulate outage: mark source unavailable; never treat as 'no enforcement / no event'.
- Simulate late corrected filing: retain both versions, update future forecasts, preserve historic as-of evaluation.
- Simulate repeated news about one primary document: count as one underlying event.
- Simulate future-dated evidence in historical training: pipeline refuses it.
- Simulate missed scheduled checks and limit exhaustion: dashboard shows stale/coverage failure with clear timestamp.
- Simulate model candidate worse than baseline: deployment refused.

## 10. Publicly verified resources and further reading (as of 2026-11-15)

- GitHub Actions scheduling limitations: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- Cloudflare Workers Cron Triggers: https://developers.cloudflare.com/workers/configuration/cron-triggers/
- Cloudflare Workers free limits: https://developers.cloudflare.com/workers/platform/limits/
- Cloudflare D1 pricing/free limits: https://developers.cloudflare.com/d1/platform/pricing/
- Cloudflare R2 pricing/free allowance: https://developers.cloudflare.com/r2/pricing/
- scikit-learn probability calibration: https://scikit-learn.org/stable/modules/calibration.html
- scikit-learn chronological cross-validation: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- Adams & MacKay, Bayesian Online Changepoint Detection (2007): https://arxiv.org/abs/0710.3742
- River ADWIN implementation: https://github.com/online-ml/river/blob/main/river/drift/adwin.py
- Dynamic hierarchical state-space forecasting (2024): https://onlinelibrary.wiley.com/doi/full/10.1002/sim.10097
- Event-History Analysis for Psychological Time-to-Event Data (2026): https://journals.sagepub.com/doi/10.1177/25152459261416470
- Online conformal prediction for nonexchangeable panel data (2026): https://arxiv.org/abs/2605.17705

**Infrastructure caveat:** Cloudflare and GitHub free tiers have quotas, scheduling constraints, and configuration requirements. The product is designed for low-cost best-effort freshness, not a contractual real-time SLA. No system has been deployed by this specification alone.
