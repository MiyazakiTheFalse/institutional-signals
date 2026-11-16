# Query-driven, multi-case research engine — first operational slice

**Status (16 November 2026):** Implemented, tested, and limited to registered offline research cases. The initial catalogue contains one real case: Thames Water / Ofwat. A synthetic second case is used in tests only. This is **not** a promise of universal knowledge or a live autonomous research agent.

## User workflow

1. Open **Ask a question** in the workstation (or use the button on the Overview).
2. Type a question, optionally select an evidence-availability date, and submit it.
3. The offline planner classifies the broad intent (evidence, timeline, relationships, forecast, explanation, other), finds a registered case through explicit aliases, then retrieves matching curated source records, observations, and already-reviewed temporal graph edges.
4. Every shown observation cites the source registry entry. Each edge shows the original evidence and the review/availability dates. Search relevance is **lexical**, not confidence.
5. If no registered case matches, the UI returns an **uncovered** status and a copyable case-planning brief describing evidence that would be required. It does not invent external sources or invoke a remote AI service.
6. Forecast/causal questions are **not answered probabilistically or causally** by keyword search. A registered forecast requires preregistration, an eligible resolved-outcome baseline, independently reviewed evidence and evidence-cutoff checks.

Search input stays in the app; no third-party search, tracking, or language-model endpoint is used.

## Data contract — `data/query_cases.json`

Each case defines:

| Field | Meaning |
| --- | --- |
| `id` | Unique stable slug, e.g. `uk-water-thames` |
| `title`, `summary` | Human-facing title and description |
| `domain`, `geography` | Domain and geographic scope |
| `aliases` | Distinguishing natural-language phrases that activate the case, with no duplicates across cases |
| `topics` | Human-declared topics for discovery/display; not an automatic classifier or new evidence |
| `source_ids` | References to existing `data/source_registry.json` entries |
| `observation_ids` | Only existing curated observations, with source IDs included in this case |
| `entity_ids` | Existing graph entities covered by the case |
| `readiness` | Must remain `research_only` until independent product readiness gates exist |

Adding another case **does not require changing the query engine**: add researched source entries and observations (as applicable), register its aliases and included record IDs, and run the normal data export/validation pipeline. Empty case evidence arrays are allowed as a plan, but the engine must return no evidence for that case.

The deterministic export embeds the validated `query_cases` array in `public/data/dashboard.json`. Raw unreviewed R2 snapshots are **not** imported into this offline register. New links and observations must pass existing provenance review processes before the curated export can change.

## Evidence integrity and historical replay

- Source metadata must pass its recorded `published_at` and `verified_at` dates before being eligible for an as-of query.
- An observation is eligible only if its dated event and **all** source records are eligible by the cutoff.
- A relationship is eligible only if it is already verified, has supporting evidence, its publication, observation, recording and review timestamps precede the cutoff, it is valid at that time, and it has not been superseded by a visible correction.
- Every returned relationship must reference an evidence source registered to the selected case.
- Each case is isolated to its declared sources/observations/entities. If two cases share an underlying document, duplicate citations are **not** independent corroboration.
- No match is not evidence of absence. A lexical match is not a verified answer, confidence score, causal mechanism or forecast.
- The existing Thames Water graph contains publisher-attribution edges. They are not automatically decision-rights, influence or misconduct edges.

## Implementation

- `src/queryEngine.ts` — pure TypeScript query planner; no browser APIs, network or storage.
- `src/Query.tsx` — accessible question editor, historical cutoff, registry chooser, results and new-case brief.
- `src/query.css` — responsive styles without new dependencies.
- `scripts/build_data.py` — schema and provenance validation of case manifests.
- `tests/query-engine.test.mjs` — Node 24 query, future-leakage, unsupported domain and synthetic second-case checks.
- `tests/test_query_cases.py` — Python provenance, alias isolation and case readiness tests.

### Validate locally

```bash
python -m unittest discover -s tests -v
python scripts/build_data.py --check
npm ci --no-audit --no-fund
node --test tests/query-engine.test.mjs
npm run build
```

The GitHub validation workflow runs these checks using only standard public-repository runners. Native desktop installers remain deliberately on-demand/version-tagged to avoid large artifact accumulation.

## What is required for the full platform

1. **Authorised case factory:** convert new queries into draft schemas, select relevant source adapters and seek explicit research scope approval, without automatically claiming a document is equivalent to a primary source.
2. **Source discovery and registration:** jurisdiction-specific official APIs, licensing, authenticated account boundaries where permitted, respectful rate limiting/backoff, data quality checks and human verification of source authority.
3. **Structured claim processing:** identify candidate assertions with precise page/section pointers; require independent review before graph promotion, with correction and disagreement handling.
4. **Cross-case provenance graph:** link institutions/documents/events using immutable references, temporal reasoning, source-independence checks and case-based permissions.
5. **Forecast eligibility and evaluation:** register decision questions prospectively; compare to transparent baselines only when sufficient resolved outcomes exist. No numerical misconduct scoring.
6. **Operational cloud and user testing:** verify actual R2/Worker, desktop integrations, authorisation, accessibility, signed installers and ongoing compute/storage limits.

**Explicit constraint:** New cases will not become comprehensive or continuously current merely because a question was typed. Each domain needs appropriate sources, evidence definitions and review rules. Questions about private or unavailable information must not produce fabricated results.
