# Institutional knowledge graph and decision intelligence — v0.1

**Status:** Initial source-publication graph and temporal replay UI implemented; authority/influence edges, live extraction, and trained graph forecasting are **not** implemented.

**First concrete slice (16 November 2026):** Four `issued` relationships connect Thames Water, Ofwat and the House of Commons EFRA Committee to documents listed in the curated source registry. These links establish only publisher attribution. Because source dates are recorded to the day rather than the second, the final second of the relevant UTC date is used conservatively when constructing availability timestamps. The edges were newly recorded/reviewed on 16 November; they cannot be used to simulate knowing these curated relationships before that review time. The public desktop Research panel presents these first edges with provenance and limitations. No legal power, private knowledge, approval right or improper influence is inferred.

## Design principle

It is not only what a system knows, but **how it knows, what each institution can know, who has decision authority, and what other organisations publicly documented as influencing that decision know**. Model information *availability and decision dependencies*, not undocumented private beliefs or guilt by association.

## Graph primitives

Nodes: `institution`, `public_body`, `formal_role`, `decision`, `document`, `claim`, `event`, `forecast`, `source`.

Edges: `oversees`, `regulates`, `funds`, `owns`, `contracts_with`, `appoints`, `has_statutory_power_over`, `issued`, `cites`, `claims`, `contradicts`, `depends_on`, `can_approve`, `can_block`, `participated_in`, `same_underlying_source_as`.

Every *real-world* edge requires:
- `edge_id`, `subject_id`, `predicate`, `object_id`
- `evidence_ids` (nonempty), `valid_from`, `valid_to` (nullable)
- `published_at`, `first_observed_at`, `recorded_at`, `review_state`
- `assertion_type`: `documented_fact`, `attributed_claim`, `hypothesis`, `disputed`
- `scope` and `limitations`, plus source independence group.

No undocumented relationships may be surfaced as verified. The graph is not a map of personal friendships, private conversations or undisclosed information. Use formal roles and organisational relationships, not dossiers on private individuals.

## Temporal semantics

`valid_from` describes when a relationship held; `published_at` when information became public; `first_observed_at` when *our system* first acquired it. Historical queries must exclude any record unavailable at the forecast's `as_of` cutoff. Later corrections remain versioned and do not rewrite past information states.

"Who knew?" is often unobservable. Replace it with testable fields:
- `publicly_available_to` / publication date;
- `formally_notified_party` only with a dated document proving notification;
- `decision_rights` as documented by statute, contract or filing;
- `unknown` when access or awareness cannot be established.

## Architecture

```text
Raw immutable documents -> extraction candidates -> source-linked claims
   -> verification / reviewer decision -> temporal entity resolution
   -> institutional relationships + decision dependencies
   -> graph feature snapshots (time-correct) -> forecast engine
   -> probability snapshots + rival explanations -> UI / briefing / API
```

Use a simple versioned JSON graph and deterministic Python validator first; add DuckDB/Parquet for local analytical joins. Graph database only after queries/scale warrant it. Any automated extraction (rules, NER, LLM) creates *candidates*, not verified facts. Deduplicate syndication and follow primary-source lineage.

## First product features

1. **Institution dossier**: documented authority, actions, dependencies, outstanding decisions.
2. **Decision map**: who can approve/block, relevant milestones and source-backed competing explanations.
3. **Evidence provenance viewer**: click any edge to inspect its underlying primary source, exact date and certainty.
4. **Temporal replay**: what was publicly knowable at a chosen date, including gaps.
5. **Impact alerts**: new verified claim -> affected graph edges -> impacted decisions -> potential forecast refresh.
6. **Research briefing**: factual changes, interpretation labelled separately, next decision window, watchpoints and uncertainty.

## Forecast features, carefully evaluated

Candidate, preregistered features: documented decision deadlines; regulator enforcement actions; statutory authority concentration; creditor voting thresholds where published; institution financial constraints; published inter-agency coordination; verified counterparty dependencies; source coverage and lag. Never score personal morality, private relationships, or purported criminal intent.

Start with sector/event base rates. Compare graph-derived features against the same baseline using prospective or temporally valid out-of-time tests, grouped by institution and underlying source. Correlation across organisations is not causation. Do not claim that adding network features improves predictions until evaluated.

## Acceptance gates

- Reject any verified edge without source provenance and time fields.
- Reject a historical query if a future-observed document leaks into earlier predictions.
- Distinguish claim vs verified fact and a regulator's allegations vs findings.
- Show documentary basis for every decision authority and dependency.
- Model contradictory sources without selecting the more convenient interpretation.
- Limit graph searches to supported institution-level facts; protect personal and sensitive data.
- Assess source independence to prevent duplicate coverage from inflating confidence.
- On correction, preserve both prior and corrected states; trigger future-only recalculation.
- Ensure deleting a discredited edge does not retroactively improve historic forecasts.

## Commercial test and defensibility

Initial buyer experiments: journalists, institutional-risk researchers, NGOs, procurement/compliance teams and sector analysts. Measure *time saved verifying a decision*, missed alerts, false-positive burden and willingness to pay before costly graph databases or sophisticated ML.

A proprietary data network is not intrinsically trustworthy. Competitive advantage should come from lawful source coverage, clear provenance, defensible historical forecasting, high retrieval reliability and a user workflow that saves time. Treat external experts as independently attributed evidence or consenting reviewers, not privileged or confidential sources by default.
