# Product acceptance — 15 November 2026

The authoritative scope is DESIGN.md plus ML_AND_FRESHNESS_ARCHITECTURE.md and the requested desktop, upload and live-storage extensions. This checklist records implementation separately from deployment. A passing build is not a production release.

## Implemented

- Native Windows, macOS and Linux packaging; sandboxed local renderer, bundled source catalogue, timeline and forecast register.
- Required-evidence cards, publisher URL and publication-date validation, bounded PDF/CSV import, SHA-256 content identity, compressed local quarantine and explicit submission queue.
- Desktop workspace connection using individual invitation keys; operating-system encrypted storage when available, memory-only fallback, disconnect and retry.
- Cloudflare Worker API with private R2 binding, per-user isolation, server-side upload validation, rate limiting, idempotent submission IDs and immutable quarantine records.
- Cloud heartbeat/source status and immutable reviewer rejection/change-request records. No endpoint exposes unscanned document bytes.
- Collector, evidence dependency gate, missing-evidence request generation and tests against unavailable/future/unverified evidence.

## Release blockers (must not be represented as completed)

1. Deploy and verify the Worker with EVIDENCE R2 binding, UPLOAD_LIMITER and AUTH_USERS secret; issue personal invitation keys. Existing R2 object credentials do not grant Worker deployment permission.
2. Verify real desktop-to-Worker upload, cross-user denial and persisted receipt on the deployed service. Local mock-R2 tests are not cloud integration tests.
3. Connect an independent malware scanning process and human verification/promotion workflow. Current reviews can request changes/reject; approval is deliberately unavailable. A PDF signature check is not malware scanning.
4. Wire verified manual evidence into the same versioned event journal and dependency gate as collected documents. Submission alone cannot unlock a forecast.
5. Complete signed Windows release and Apple signing/notarization; test installation on clean supported OS machines. Current packages are development builds.
6. Implement and validate the remaining architecture acceptance tests for append-only forecasts, historical replay, model comparison and promotion. There are no trained production models or accuracy claims.
7. Replace the interim GitHub polling schedule with the designed Worker schedule/reconciliation/watchdog, or document and accept its lower freshness guarantee.

## Operator deployment

Use Node with dependencies installed, then `npx wrangler deploy --config cloud/wrangler.jsonc` after authenticating to the correct Cloudflare account. Set AUTH_USERS using the platform secret store, never a committed file. Shape: a JSON array of records with `id` (letters/digits/underscore/hyphen), `role` (`contributor` or `reviewer`), and `token_sha256` (SHA-256 of a cryptographically random 32-byte base64url invitation key). The actual invitation key belongs only to that person. Remove a record to revoke access. Do not reuse an R2 access key as an invitation.

The API fails closed without bindings, credentials or upload limits. No CORS is enabled: desktop network calls originate in the protected main process. Workspace addresses currently allow only HTTPS workers.dev hosts, no ports, redirects or credentials. This initial invitation flow is for a controlled pilot, not public self-service registration.

## Honest end-user behaviour

Offline: browse bundled research and import evidence with provenance. Connected: refresh collector health, submit requested evidence and confirm receipt in cloud quarantine. All forecasts remain on hold until verified evidence and model eligibility are established. Do not label a stored or collected document “verified” solely because it exists.
