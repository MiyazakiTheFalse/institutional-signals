# Contributing to Institutional Signals

Institutional Signals is a research product with public claims and forecasts. Correctness, provenance, reversibility and plain explanations take priority over feature throughput.

## Development workflow

1. Create a short-lived branch from `main` (e.g. `feat/...`, `fix/...`, `docs/...`).
2. Make the smallest coherent change; do not mix speculative refactoring with a critical bug fix.
3. Add/adjust tests for every behaviour change. For evidence, forecasting, security and time semantics, include a failure or adversarial case.
4. Run the standard quality gate, Python tests, desktop/cloud tests and frontend build. If tooling is unavailable, say so explicitly in the PR.
5. Open a PR with the template. Do not merge while required checks fail. Prefer a second reviewer for high-risk changes.
6. Merge only after tests, documentation, data contract and rollback have been considered. Do not force-push shared release branches.

### Local checks

```bash
python scripts/quality_gate.py
python scripts/build_data.py --check
python -m unittest discover -s tests -v
npm ci --no-audit --no-fund
node --test desktop/test-validation.cjs desktop/test-provenance.cjs cloud/test-worker.mjs
npm run build
```

The repository commits `package-lock.json`. Use `npm ci` (not `npm install`) for validation and packaging; deliberately update the lockfile only when dependencies change, with a reviewed PR.

## Risk tiers

- **Low:** documentation, UI copy, cosmetic styling. Test what changed.
- **Medium:** component refactors, ingestion adapters, source registries, deployment configuration. Include regression tests and a rollback path.
- **High:** historical replay, forecast locking, model promotion, public accusations, source validation, credentials, data deletion, security boundaries, new third-party services. Require an architecture decision record (ADR), explicit evidence/test cases, security/privacy review, and an independent review when available. If nobody can review, leave a clear written self-review and do not silently weaken controls.

Use `docs/adr/` to record the decision, alternatives, consequences and reversal conditions for changes to architecture, dependencies, persistent schema or trust boundaries.

## Research and data integrity

- Raw evidence is immutable; corrections add a new record and link to the superseded item.
- Do not turn extraction candidates into verified assertions without a traceable review step.
- Every verified assertion needs an attributable source, timestamp and limitations.
- Test historical queries with publication **and first-seen** timestamps. Future information must never enter earlier forecasts.
- Preserve model, data, features, decision rules and evaluation cutoffs per forecast. No performance claims without resolved outcomes and baselines.
- Changes to stored data require a migration plan, backward-compatibility check, and explicit recovery or rollback process.
- Do not add personal dossiers, confidential material or unverified claims of wrongdoing.

## Cost constraints

The accepted engineering budget for GitHub testing is **£0 of billable usage**. Keep the repository on standard free public-repository runners; never add larger runners. Installer builds are on-demand, version-tag or desktop-build changes to `main`; they do not run for ordinary PRs. Artifacts expire after one day. Treat GitHub Actions storage as a separate potential metered cost. Account-level spending limits must be configured by the owner in GitHub billing; code alone cannot enforce a £0 bill. If the repository becomes private, stop and review its CI cost before running automation.

The local-check commands above are the fallback when GitHub Actions is disabled or unavailable.

## Dependencies and releases

- Prefer built-in or existing libraries; justify new production dependencies in the PR.
- Dependabot proposals are reviewed and tested, not auto-merged.
- Do not commit secrets, raw private evidence, build outputs or local archives.
- Version releases deliberately; create a draft release, validate installers on native OSs, then publish.
- Production distribution requires dependency locking and an explicit code-signing/notarisation decision.

See `SECURITY.md` and `docs/ENGINEERING_POLICY.md` for vulnerability handling and release gates.
