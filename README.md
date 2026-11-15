# Institutional Signals

**Open, auditable institutional behaviour research.** Initial case study: Thames Water and its regulatory environment (UK).

> Research prototype, not an accusation engine or financial advice. Evidence is linked; hypotheses are labelled; forecasts have explicit resolution rules. No model performance is claimed before sufficient outcomes are recorded.

## First-pass product

The implementation now includes cross-platform desktop packaging, provenance-aware imports, a submission queue, private R2 intake API, live collector status, operator scanning/review, a temporal institutional graph, and a gated experimental forecast core. See [product acceptance](docs/PRODUCT_ACCEPTANCE.md) for what is implemented versus deployed and verified. No trained predictive performance is claimed.

The **Build desktop installers** Actions workflow produces Windows x64, Intel/Apple Silicon macOS, and Linux x64 development packages. The **Validate cloud service** workflow verifies Worker bundling without deploying or granting access. Deployment requires a scoped Cloudflare deployment credential and individually provisioned invitation keys.

## Curated research foundation

- Static React + TypeScript dashboard showing verified *source records*, event chronology, and forecast-register status.
- Version-controlled source register and prediction protocol.
- Python script that validates source entries and exports a compact JSON dataset for the frontend.
- Unit tests, automated consistency checks, GitHub Actions workflow.
- No paid AI API, server, database, or API key required.

## Quick start

Live collection and compressed Cloudflare storage are implemented in [`scripts/collect.py`](scripts/collect.py). See [`docs/LIVE_COLLECTION.md`](docs/LIVE_COLLECTION.md) for activation, credentials, storage layout and deployment limits. The scheduled collector remains disabled until R2 secrets and `COLLECTION_ENABLED=true` are configured.

```bash
python3 scripts/build_data.py
python3 -m unittest discover -s tests -v
npm install
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
- [`docs/BACKLOG.md`](docs/BACKLOG.md) - staged delivery plan and acceptance tests.
- [`data/source_registry.json`](data/source_registry.json) - vetted source catalogue.
- [`data/observations.json`](data/observations.json) - sourced initial events.
- [`data/forecasts.json`](data/forecasts.json) - empty, pending forecast register.
- [`scripts/build_data.py`](scripts/build_data.py) - validation and static export.

## Important limitations

- The dashboard's bootstrap data is curated. The separate live-collection workflow archives source-page contents to R2 once activated; the dashboard is not yet connected to that archive.
- Initial sources are verified as of **15 November 2026**. Their linked content may change. Version history and `observed_at` must be retained for future collections.
- No numerical predictive accuracy or corruption probability should be shown until data support them.
- Some data may be under OGL v3.0; **verify each dataset's reuse terms individually**. Linking to an article does not imply the entire article can be copied.

## Deployment / repository status

Repository: https://github.com/MiyazakiTheFalse/institutional-signals. Dashboard deployment requires linking the repository to Cloudflare Pages. Collection activation is separate; follow the live-collection setup above.

## Licences

Project code is provided under the MIT Licence (see `LICENSE`). Source materials remain under their original rights and terms; link and attribute sources.
