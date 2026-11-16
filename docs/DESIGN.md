# Institutional Signals — Product and technical design

**Version:** 0.1 (research prototype)  
**Date:** 15 November 2026  
**Project owner:** Repository owner  
**Initial case:** Thames Water / Ofwat / UK water-sector regulation  
**Status:** Original v0.1 design baseline, retained for research rationale; implementation has advanced to the UX v0.3 preview but is **not** a production intelligence service.

**Implementation note (16 November 2026):** The current application has six task-focused views, an interactive graph with four curated publisher-attribution edges, recovered Parliament document retrieval, an evidence change feed and experimental forecast gates. This original design's references to a minimal static dashboard describe the starting architecture, not current release status. Consult [Product acceptance](PRODUCT_ACCEPTANCE.md), [UX v0.3](UX_WORKSTATION_V03.md) and [Delivery backlog](BACKLOG.md) for current implementation and unverified production blockers.

## 1. Executive summary

Institutional Signals is an evidence-based, auditable platform for studying and forecasting **observable institutional decisions**. It connects dated primary documents, institutional incentive hypotheses, events and preregistered probabilistic predictions. It explicitly does **not** infer that named persons or organisations are corrupt, criminal, or acting improperly without evidence.

A useful minimum product is a trustworthy source catalogue, dated events, and a forecast ledger whose questions, dates, resolution rules and outcomes can be independently checked. This is more credible than an opaque numerical 'corruption score', more attainable within a £0 recurring-infrastructure budget, and better suited to an academic research portfolio.

## 2. Target users and jobs to be done

- **Researcher/analyst:** Identify what an institution did, what evidence supports that record, how incentives could explain it, and what competing hypotheses exist.
- **Journalist/civic reader:** Follow primary-source links and verify whether a prediction was stated before the outcome.
- **Student/evaluator:** Reproduce calculations, compare forecasts with baselines, and document analytical limitations.
- **Potential professional buyer (later):** Receive timely, carefully sourced briefings about upcoming institutional decisions. Commercial demand is untested.

## 3. Goals, non-goals and success criteria

### Goals (MVP)

1. Host a readable case dashboard with source provenance and chronological events.
2. Export structured records from version-controlled JSON and fail builds on invalid references.
3. Preserve a separate forecast register and full resolution criteria.
4. Run tests on every push; deploy a static frontend without API keys, billing or backend.
5. Make uncertainties, source bias and corrections visible.

### Non-goals (MVP)

- Automatic claims of corruption or fraud; personality profiling of public employees; access to non-public material; trading recommendations.
- Realtime autonomous surveillance, opaque LLM summarisation, paid inference, automated legal complaints.
- Production-grade event ingestion or a trained predictive classifier: there are not yet sufficient labelled institutional decision outcomes.

### Acceptance criteria

- Local Python tests all pass; static data export is deterministic.
- `npm run build` produces `dist/` using Node.js 20+.
- All displayed claims link to source IDs resolving to original URLs, including published dates.
- No unsourced numerical model confidence or accuracy statistic appears.
- Zero paid accounts or credentials are required to run the starter.

## 4. Research question and conceptual model

**Research question:** Do preregistered indicators of financial constraints, regulatory pressure, public scrutiny and negotiating leverage improve prediction of observable institutional decisions relative to naive baselines?

**Conceptual chain:** institution -> decision opportunity -> documented constraints/incentives -> competing behavioural hypotheses -> forecast -> observed decision -> error analysis.

Candidate hypotheses include: financial pressure makes short-term refinancing more likely; parliamentary pressure may increase public commitments to enforcement; regulators may prefer gradual intervention over sharp discontinuities because of service-continuity risk. Each remains a testable hypothesis, never a finding of improper intent.

## 5. System architecture

```text
Ofwat / Parliament / Thames Water / Companies House (future)
                         |
        primary-document references + manual curation (MVP)
                         |
              data/source_registry.json
              data/observations.json
              data/forecasts.json
                         |
           Python validation/export (stdlib)
                         |
          public/data/dashboard.json
                         |
        React + TypeScript + Vite static UI
                         |
               Cloudflare Pages (later)

GitHub Actions: tests on push/PR; periodic validation only.
```

The frontend consumes committed static JSON. No browser-held secret, serverless bill or dynamic SQL database is needed. Separate stages can later be added for ingesting bulk Ofwat data, using DuckDB for offline analysis, and a read-only API if customer demand warrants it.

### Tech choices

| Layer | Choice | Why now | Upgrade trigger |
|---|---|---|---|
| UI | React, TypeScript, Vite, CSS | Static, fast, familiar, easy Pages deployment | Need richer interaction or SSR |
| Data | JSON in Git | Public audit trail, few records, low complexity | >10k records or concurrent editing |
| Export | Python 3.11+ stdlib | Fast setup, deterministic validation, no secrets | Excel/Parquet scale |
| Testing | unittest, TypeScript compiler, Vite | No Python extras, reproducible checks | Wider pipeline complexity |
| CI | GitHub Actions | Tests and audit trail | Build limits, costs, governance |
| Hosting | Cloudflare Pages free | Static website + HTTPS | Service-level / dynamic requirements |
| Analysis later | DuckDB, pandas, scikit-learn | Offline, explainable, no per-token API fee | Sufficient historical outcome sample |

## 6. Domain and data model

**Source:** `id`, `title`, `publisher`, `published_at`, `url`, `type`, `reliability_note`, `access_note`, `verified_at`.

**Observation:** `id`, `date`, `subject`, `event_type`, `summary`, `source_ids[]`, `status`. Facts and party statements are distinct types; no conclusion about motives is stored as fact.

**Forecast:** `id`, `question`, `institution`, `created_at`, `close_at`, `resolve_by`, `probability` (0–1 or null in draft), `resolution_rule`, `baseline_probability`, `evidence_source_ids[]`, `status`, `outcome`, `outcome_source_ids[]`, `rationale`, `rival_explanations`. Initial register is empty until a question can be locked against later evidence.

Future append-only additions: `collected_at`, `source_hash`, `document_version`, `correction_of`, `resolver_id`, `confidence_interval`, `source_licence`.

## 7. Evidence, attribution and risk controls

- Define an evidence hierarchy: official decision/filing; oversight report; independently reported account; analyst hypothesis.
- Record date of publication separately from date first collected. Never use information published after the forecast cutoff to rationalise an earlier prediction.
- Cite original material using links and short original summaries; verify each source's licence before mirroring full text or datasets.
- Give institutions an appropriate right to respond before publishing high-stakes allegations; issue visible corrections. Separate parliamentary concerns from findings of fact.
- Avoid private-person data, speculation about individuals and automatic accusations of corrupt conduct.
- Treat source changes, scraping blocks, rate limits and removed documents as errors, never permission to invent data.

## 8. Forecast protocol and evaluation

1. Choose a binary, externally observable decision with a date and mutually exhaustive resolution conditions.
2. Register the forecast and evidence cutoff *before* subsequent source publication.
3. Specify plausible competing explanations and a baseline before estimating probability.
4. Freeze the locked record in Git history. If revised, create a new linked forecast; do not overwrite history.
5. Resolve using an independent published source and disclose unresolved/ambiguous cases.
6. Evaluate binary forecasts with Brier score `mean((p - y)^2)` where `y` is 0 or 1; compare to the baseline. Display outcome count and interval estimates before claiming predictive skill.
7. Use temporal cross-validation for later model development. Watch class imbalance, selection bias, leakage, confounds and institutional heterogeneity.

A few anecdotal correct predictions would **not** establish predictive validity. For academic research, formal ethics and data governance review may be appropriate depending on the study design and participants.

## 9. First case: Thames Water

**Verified starting documents:**
- EFRA Committee report dated 18 September 2026 on special administration and creditor influence.
- Ofwat 2025–26 operational performance data published 29 October 2026.
- EFRA Committee report/news dated 4 November 2026 calling for safeguards against regulatory capture.
- Thames Water 9 November 2026 statement describing a proposed debt-maturity extension and expected court/creditor milestones.

The 9 November company statement lists a **27 Nov 2026 convening hearing**, **17 Dec 2026 creditor meetings**, **13 Jan 2027 sanction hearing**, and an effective-date target in the week beginning **1 Feb 2027**, all contingent and subject to change. These are **company-stated plans, not confirmed future events**.

Potential future forecast target: whether a particular specified debt-extension plan receives court sanction by a stated deadline. Do not enter a numerical probability until legal definitions, available evidence and baseline are documented.

## 10. Functional scope

### MVP screens

1. **Overview:** project definition, status, limitations and key dates.
2. **Evidence:** source register with publisher, publication date and direct link.
3. **Timeline:** chronological observations and source IDs.
4. **Forecast ledger:** draft/locked/resolved status and rule; empty-state until predictions are registered.
5. **Methods:** evidence standards, correction process and research protocol links.

### Accessibility and UX

Responsive at 360px mobile width; readable contrast; semantic headings and links; keyboard access; descriptive timestamps and externally linked source labels. Never use red/green alone to distinguish evidence quality or forecast outcomes.

## 11. Security and operating model

- Public website never embeds a Companies House API key. Use GitHub Actions secrets for any future API authentication; use minimum permissions and `contents: read` on routine checks.
- Do not scrape password-protected creditor data. Respect robots, licences and terms.
- Pull requests and tests for dataset changes; no unattended automatic publication of high-risk interpretation.
- No personal account information or contact details in repository data. Keep user correspondence with institutions separate unless explicitly cleared for publication.
- For public releases, verify source URLs, security audit dependencies and link policy.

## 12. Cost model

| Item | MVP monthly recurring cash cost | Conditions |
|---|---:|---|
| GitHub repository | £0 | Free plan, storage/usage within limits |
| GitHub Actions | £0 | Standard runner allocations; public repositories generally unrestricted for standard runners; private usage has allowances |
| Cloudflare Pages | £0 | Free build/asset limits; no domain purchase |
| Python and npm packages | £0 | Open-source components, no proprietary API calls |
| Companies House data | £0 API access | Optional account/API key; respect conditions and rate limits |
| Human research/maintenance | Not £0 in labour | Time, diligence, verification and possible licensing needs remain |

**Budget claim:** £0 cash recurring infrastructure at modest MVP usage, not zero opportunity cost or guaranteed permanent pricing.

## 13. Delivery roadmap and decisions

**P0: Initial scaffold (provided).** Data model, verified source register, starter dashboard, validator, tests, CI, docs, README, private repository creation instructions.

**P1: Live publication.** Create repo, run CI, connect Cloudflare, accessibility and content review. Publish methods and data corrections policy.

**P2: First registered forecast.** Freeze precise prediction question, probability, baseline and resolution rule in a commit before deadline.

**P3: Repeatable ingestion.** Parliament API endpoint validation, Ofwat spreadsheet import and source snapshots with licensing and schema tests.

**P4: Research evaluation.** Assemble multi-case historical dataset, compare simple baselines, make reproducible results and solicit peer review.

**P5: Commercial research trial.** Test briefing usefulness and willingness to pay without overstating accuracy or providing unsupported investment guidance.

## 14. Critical risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| False allegation or reputational harm | High | No wrongdoing score; distinguish allegations, oversight findings and source-backed facts |
| Predictive overfitting / post hoc storytelling | High | Register in advance; baseline; temporal splits; disclose misses |
| Data licensing / copyright | Medium-high | Link and attribute; review individual dataset licence before redistribution |
| Stale or revised documents | Medium | Keep original publication date + fetched-at; later archive snapshots and hashes |
| Privacy/security | High | No personal profiles, no secrets in browser or Git |
| £0 platform limit changes | Medium | Static portable build; dependency-light architecture; monitor quotas |
| Commercial demand absent | Medium | Test customer needs before adding infrastructure |
| Inaccessible source or schema change | Medium | Mark unavailable; halt changes rather than fabricate observations |

## 15. Open decisions

- Whether the first public release should be under the existing personal GitHub account or a separate organisation.
- Public-facing brand, logo and domain (none required to begin).
- Whether repo should remain private through initial factual review; recommended: **private first**.
- Who independently checks the first formal forecast's resolution and what documented baseline is defensible.

## 16. References and supporting resources

See `docs/RESOURCES.md` for verified URLs, access conditions and developer documentation. The references are integral to the design but remain the property of their original publishers.
