# Institutional Signals

**Open, auditable institutional behaviour research.** Initial case study: Thames Water and its regulatory environment (UK).

> Research prototype, not an accusation engine or financial advice. Evidence is linked; hypotheses are labelled; forecasts have explicit resolution rules. No model performance is claimed before sufficient outcomes are recorded.

## Current product (UX v0.3 preview)

The implementation includes cross-platform desktop packaging, provenance-aware imports, a submission queue, private R2 intake API, collector status, operator scanning/review, a temporal institutional graph, and a gated experimental forecast core. The UX v0.3 workstation provides **Overview, Timeline, Relationships, Evidence, Forecasts and Workspace** views, searchable curated records and a selectable graph with source provenance and historical cutoffs. Its seven nodes and four reviewed edges initially show **publisher attribution only**, not influence or decision rights. See [product acceptance](docs/PRODUCT_ACCEPTANCE.md) and [UX acceptance](docs/UX_WORKSTATION_V03.md) for what is implemented, tested and still unverified. No trained predictive performance is claimed.

The **Build desktop installers** Actions workflow produces Windows x64, Intel/Apple Silicon macOS, and Linux x64 development packages. The **Validate cloud service** workflow verifies Worker bundling without deploying or granting access. Deployment requires a scoped Cloudflare deployment credential and individually provisioned invitation keys.

## Question-driven research (experimental)

The workstation now has an **Ask a question** view powered by an offline, case-registered retrieval engine. Enter a question and historical evidence cutoff to find relevant curated observations, publisher references and reviewed graph relationships. Unsupported domains return an explicit **uncovered** status and a research-brief template, not invented evidence.

The query engine is reusable across cases: new jurisdictions or institutional sectors can register aliases, curated source IDs, observations and graph entities in `data/query_cases.json`, without changing retrieval code. A synthetic second domain is covered by regression tests; **only the UK water-sector case is included in the shipped research data**.

This is keyword retrieval and provenance lookup, **not** general open-web question answering, automated source discovery, trained predictions, causality analysis or live institutional coverage. Forecasts remain gated, and no additional paid service is required. Read [the query-engine scope and extension contract](docs/QUERY_ENGINE_V04.md).

## Curated research foundation

- Static React + TypeScript intelligence workstation showing curated source records, searchable event chronology, evidence requirements, inspectable institutional relationships and forecast-register status.
- Version-controlled source register and prediction protocol.
- Python script that validates source entries and exports a compact JSON dataset for the frontend.
- Unit tests, automated consistency checks, GitHub Actions workflow.
- No paid AI API, server, database, or API key required.

## Quick start

Live collection and compressed Cloudflare storage are implemented in [`scripts/collect.py`](scripts/collect.py). See [`docs/LIVE_COLLECTION.md`](docs/LIVE_COLLECTION.md) for activation, credentials, storage layout and deployment limits. The scheduled collector is gated by R2 credentials and `COLLECTION_ENABLED=true`. A passing validation build is not proof of end-to-end live deployment; the source-access gates still report incomplete coverage on Ofwat and other restricted original URLs.

```bash
python3 scripts/build_data.py
python3 -m unittest discover -s tests -v
npm ci
npm run dev
```

Open the local Vite URL shown by `npm run dev`. To build for Cloudflare Pages:

```bash
npm run build
```

Cloudflare Pages settings: **root directory `/`**, build command `npm run build`, output directory `dist`, production branch `main`.

## Freshness and modelling research (design, not live ingestion)

- [`docs/ML_AND_FRESHNESS_ARCHITECTURE.md`](docs/ML_AND_FRESHNESS_ARCHITECTURE.md) — cross-institution data freshness guarantees, mathematical model choices, leakage prevention and rollout.
- [`scripts/freshness.py`](scripts/freshness.py) — tested source-status logic; deliberately does not perform network retrieval.
- [`scripts/probability.py`](scripts/probability.py) — tested transparent baseline probability and scoring helpers; not a trained ML model.
- [`config/source_registry.example.yaml`](config/source_registry.example.yaml) — example future source monitoring configuration.
- [`architecture/PREDICTION_AND_FRESHNESS_CONTRACT.json`](architecture/PREDICTION_AND_FRESHNESS_CONTRACT.json) — future storage contract and invariants.

**Important:** The R2 collector archives source-page changes for review. It does not yet extract verified events or automatically update forecasts. A weekly data-validation workflow alone does not refresh published evidence.

## Repository guide

- [`docs/DESIGN.md`](docs/DESIGN.md) - full technical/product specification and research methodology.
- [`docs/RESOURCES.md`](docs/RESOURCES.md) - verified primary-source, platform and methodological links.
- [`docs/SETUP.md`](docs/SETUP.md) - GitHub creation, publishing and Cloudflare setup.
- [`docs/RESEARCH_PROTOCOL.md`](docs/RESEARCH_PROTOCOL.md) - forecasting/scoring and evidence standards.
- [`docs/BACKLOG.md`](docs/BACKLOG.md) - current delivery blockers and acceptance gates.
- [`docs/UX_WORKSTATION_V03.md`](docs/UX_WORKSTATION_V03.md) - workstation navigation and accessibility acceptance checklist.
- [`docs/QUERY_ENGINE_V04.md`](docs/QUERY_ENGINE_V04.md) - query-case registry, offline retrieval guarantees and the general-purpose research roadmap.
- [`docs/SOURCE_ACCESS_STRATEGY.md`](docs/SOURCE_ACCESS_STRATEGY.md) - official fallback routes, Parliament PDF recovery and remaining Ofwat restrictions.
- [`data/source_registry.json`](data/source_registry.json) - vetted source catalogue.
- [`data/observations.json`](data/observations.json) - sourced initial events.
- [`data/forecasts.json`](data/forecasts.json) - empty, pending forecast register.
- [`scripts/build_data.py`](scripts/build_data.py) - validation and static export.

## Important limitations

- The dashboard's bootstrap research data is curated and static; the optional authenticated desktop Workspace can show collector health and unreviewed source-change descriptors when the private service is connected. Curated observations and graph assertions are **not automatically promoted** from raw archived documents.
- Initial sources are verified as of **15 November 2026**. Their linked content may change. Version history and `observed_at` must be retained for future collections.
- No numerical predictive accuracy or corruption probability should be shown until data support them.
- Some data may be under OGL v3.0; **verify each dataset's reuse terms individually**. Linking to an article does not imply the entire article can be copied.

## Deployment / repository status

Repository: https://github.com/MiyazakiTheFalse/institutional-signals. No published production release has been accepted. Native installer development builds use manual or version-tag workflows. Cloudflare Pages publication and Worker/R2 activation require independent configuration and live acceptance testing; see the product checklist.

## Licences

Project code is provided under the MIT Licence (see `LICENSE`). Source materials remain under their original rights and terms; link and attribute sources.
