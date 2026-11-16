# Source change review feed (v0.3)

## What is implemented

Every successful source-content change is still stored as immutable gzip content addressed by SHA-256 and recorded in an immutable run manifest. In addition, the collector now persists up to 100 **recent unreviewed source change descriptors** in the latest status snapshot. This is a convenience index, not a durable replacement for the run archive.

Descriptors include only: `source_id`, `observed_at`, `sha256`, `previous_sha256`, `coverage_scope` and the constant review state `unreviewed_content_change`.

The authenticated workspace `GET /v1/status` exposes this bounded feed and safe categorized retrieval diagnostics. Raw document bytes, object keys, internal failure text, client credentials, and full source URLs are not exposed through that feed. The desktop workspace explicitly labels changes as unreviewed.

## Why these safeguards matter

A 200 response means a source returned bytes, not that those bytes establish an institutional decision. Repeated 304 checks are recorded as successful polls but not new events. A 403 on the original source remains a failure even if a nearby official API or alternate document can be retrieved. Missing collection or review coverage keeps affected forecasts on hold.

A corrected document is archived with a new hash and a reference to the prior hash. Historical forecasts must not be rewritten. A future evidence-review service must create **separate, append-only review decisions**, referencing hashes and source assertions; it must never overwrite an earlier judgement.

## Failure codes

| Code | Meaning |
|---|---|
| `http_403` | Source HTTP request was forbidden; no inference about why |
| `http_429` | Rate limiting; respect retry instructions and backoff |
| `http_5xx` | Source-side HTTP error |
| `robots_disallowed` | Source robots policy forbids automated retrieval |
| `validation_error` | Retrieval succeeded or returned data but integrity/shape requirements failed |
| `network_error` | Network, timeout, or other transport failure |

Only these simple categories are exposed to workspace users. The private collector archive retains detailed diagnostics for the operator. Never try to bypass access controls, change the user agent to impersonate a browser, or obscure automated fetching.

## Operational verification

```bash
python -m unittest discover -s tests -v
node --test cloud/test-worker.mjs desktop/test-validation.cjs desktop/test-provenance.cjs
python scripts/build_data.py --check
npm ci
npm run build
```

To exercise the collector without Cloudflare:

```bash
python scripts/collect.py --store local
```

Its local `.collection/` directory is deliberately gitignored. It may encounter real source 403/429 responses and exit nonzero when required sources are unavailable; that is a correct signal of incomplete coverage, not proof that the snapshot logic failed.

To see live workspace results, the owner must configure and activate the private R2 bucket, secrets and Worker; collection is not activated merely by installing the desktop app.

## Remaining work

- Convert candidate document snapshots into structured *candidate claims* with original document/page pointers, without automatic promotion.
- Provide a reviewer interface with independent verification, rejection and correction histories.
- Publish sanitized, verified claims to versioned graph edges after review.
- Add a full history search using durable run manifests (the recent feed is deliberately capped).
- Resolve the original publisher 403 issues through documented official APIs, permissions or manual evidence submission; never call an alternative publication equivalent without checking its scope.
- Test live R2/Worker deployment and reliability against quotas; automatic collection cannot be claimed live until verified.
