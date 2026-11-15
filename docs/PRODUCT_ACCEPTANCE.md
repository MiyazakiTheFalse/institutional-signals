# Product acceptance — 15 November 2026

The authoritative scope is DESIGN.md plus ML_AND_FRESHNESS_ARCHITECTURE.md and the requested desktop, upload and live-storage extensions. This checklist records implementation separately from deployment. A passing build is not a production release.

## Implemented

- Native Windows, macOS and Linux packaging; sandboxed local renderer, bundled source catalogue, timeline and forecast register.
- Required-evidence cards, publisher URL and publication-date validation, bounded PDF/CSV import, SHA-256 content identity, compressed local quarantine and explicit submission queue.
- Desktop workspace connection using individual invitation keys; operating-system encrypted storage when available, memory-only fallback, disconnect and retry.
- Cloudflare Worker API with private R2 binding, per-user isolation, server-side upload validation, rate limiting, idempotent submission IDs and immutable quarantine records.
- Cloud heartbeat/source status, a scheduled watchdog, and immutable reviewer rejection/change-request records. No endpoint exposes unscanned document bytes.
- Collector, evidence dependency gate, missing-evidence request generation and tests against unavailable/future/unverified evidence.
- Temporal institutional graph validation/replay, source independence and correction lineage, descriptive graph features and affected-decision traversal. UI provides institution selection, as-of date, provenance inspection and a factual briefing scaffold. The graph intentionally has no invented relationships.
- Experimental baseline forecast generation with independent resolved-outcome minimum, no-future-information checks, immutable content-addressed snapshots, Brier/log-loss comparison and a conservative candidate screening gate. These are tested components, not a trained production model or automatically published forecast.
- Operator ClamAV scan command/workflow and human verification command. Exact hashes and recent signatures are required; scanner errors fail closed. Verified manual evidence can fill unavailable collection routes for a bounded freshness interval, then expires back to hold.
- Scheduled research orchestration consumes explicitly registered targets, matching outcome families and reviewed evidence, then stores immutable eligible baseline snapshots. Target/outcome registers are initially empty; no probability is invented to populate the dashboard.

## Release blockers (must not be represented as completed)

1. Deploy and verify the Worker with EVIDENCE R2 binding, UPLOAD_LIMITER and AUTH_USERS secret; issue personal invitation keys. Existing R2 object credentials do not grant Worker deployment permission.
2. Verify real desktop-to-Worker upload, cross-user denial and persisted receipt on the deployed service. Local mock-R2 tests are not cloud integration tests.
3. Exercise the ClamAV and operator verification path on real quarantined documents. Web reviewer approval remains disabled; trusted operators use scripts/review_evidence.py after independently checking the source/content. A PDF signature check is not malware scanning.
4. Validate the manual-evidence-to-collector integration in the deployed environment. Immutable review records now feed the collector dependency gate; submission alone cannot unlock a forecast.
5. Complete signed Windows release and Apple signing/notarization; test installation on clean supported OS machines. Current packages are development builds.
6. Assemble reviewed institutional relationships, labelled historical outcomes and preregistered forecast targets. Connect automatic forecast orchestration only after prospective/temporal evaluation; hierarchical models, calibration and drift-driven retraining remain future work.
7. Replace the interim GitHub polling schedule with the designed Worker schedule/reconciliation/watchdog, or document and accept its lower freshness guarantee.

## Operator evidence workflow

1. Submit through the desktop to private quarantine; retain the returned submission ID and owner.
2. Run the `Scan quarantined evidence` GitHub workflow for that owner and submission. It installs ClamAV, updates signatures and writes an immutable scan record. This workflow has not yet been validated against a live uploaded document.
3. Independently verify the publication, exact content, case requirement and underlying primary-document identity. Inspect untrusted files only in an appropriately isolated review environment.
4. Run `python scripts/review_evidence.py --owner OWNER --submission UUID --scan-key scans/OWNER/UUID/HASH.json.gz --source SOURCE_ID --reviewer REVIEWER --primary-document-id DOCUMENT_ID --confirm-content-verified` with operator R2 credentials in the environment. Never place credentials in command arguments or the repository.
5. The next collector pass loads the immutable review record. Manual freshness is capped at three source polling intervals or 24 hours, whichever is shorter. This is an explicit conservative policy for the pilot, not a claim that an old publication is intrinsically obsolete.

A clean malware scan and content verification are separate gates. The workflow does not extract claims or invent graph relationships. Source-linked graph edges must be entered into data/knowledge_graph.json and pass validation before export.

## Operator deployment

Use Node with dependencies installed, then `npx wrangler deploy --config cloud/wrangler.jsonc` after authenticating to the correct Cloudflare account. Set AUTH_USERS using the platform secret store, never a committed file. Shape: a JSON array of records with `id` (letters/digits/underscore/hyphen), `role` (`contributor` or `reviewer`), and `token_sha256` (SHA-256 of a cryptographically random 32-byte base64url invitation key). The actual invitation key belongs only to that person. Remove a record to revoke access. Do not reuse an R2 access key as an invitation.

The API fails closed without bindings, credentials or upload limits. No CORS is enabled: desktop network calls originate in the protected main process. Workspace addresses currently allow only HTTPS workers.dev hosts, no ports, redirects or credentials. This initial invitation flow is for a controlled pilot, not public self-service registration.

## Honest end-user behaviour

Offline: browse bundled research and import evidence with provenance. Connected: refresh collector health, submit requested evidence and confirm receipt in cloud quarantine. All forecasts remain on hold until verified evidence and model eligibility are established. Do not label a stored or collected document “verified” solely because it exists.
