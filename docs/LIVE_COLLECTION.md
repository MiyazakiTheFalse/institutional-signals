# Live collection and Cloudflare R2

## What this release does

`scripts/collect.py` polls the six registered primary documents and Thames Water's news index. It respects robots exclusions, uses ETag/Last-Modified conditional requests, and records successful checks separately from publication age. A source-page change becomes an **unreviewed content change**, not a verified new event or a forecast update. Index snapshots detect changes but do not yet follow links to archive every newly published article.

Raw response bytes are SHA-256 addressed and gzip compressed. Compression is lossless; its ratio depends on the source. Only new content hashes are uploaded. Each run has a separate compressed journal; corrections retain the previous hash and original bytes. Checkpoints and health reports are compressed JSON. No raw archive is committed to Git.

## Storage layout

- `raw/sha256/xx/<sha256>.gz`: immutable compressed source bytes.
- `runs/YYYY/MM/DD/<time>-<uuid>.json.gz`: immutable run manifests with provenance and changes.
- `state/latest.json.gz`: current conditional headers, retry state and last successful checks.
- `status/latest.json.gz`: latest source health and coverage report.

Only one writer may use a bucket. The Actions concurrency group serializes scheduled/manual runs. Do not run a second collector against that bucket simultaneously. A failed durable run upload does not advance the checkpoint. Scheduled Actions can run late; health status must be recalculated against the current clock by any reader rather than trusting an old `current` label indefinitely.

## Cloudflare setup

1. Create a **private Standard** R2 bucket named `institutional-signals-evidence`. Do not enable a public URL for the raw archive.
2. Create R2 S3 API credentials with **Object Read & Write**, limited to this bucket. Keep the secret out of chat and Git. Credential creation requires user approval in the browser.
3. In GitHub repository Settings → Secrets and variables → Actions, add `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, and `R2_SECRET_ACCESS_KEY` as secrets. The bucket secret is `institutional-signals-evidence`.
4. Add repository variable `COLLECTION_ENABLED` with value `true` after credentials are ready.
5. Open Actions → Collect and archive public sources → Run workflow. Confirm the run uploads a manifest, snapshots and a health report into R2. Failures remain visible and must not be reported as successful collection.

The workflow checks every 30 minutes; individual documents target 60 minutes, and the news index targets 30 minutes. Retries back off and honor HTTP 429 Retry-After. A forbidden source or unavailable robots file is reported as failed, without bypassing access restrictions.

## Local use

```bash
python -m unittest discover -s tests -v
python scripts/collect.py --store local
# For cloud mode, set the four environment variables first:
python -m pip install -r requirements-collection.txt
python scripts/collect.py --store r2
```

Local output goes into ignored `.collection/`. Environment variables must be supplied by the shell or Actions; `.env` is not loaded automatically.

## Deployment status and next work

The collector and local storage logic have automated tests. R2 integration requires a successful real cloud run before claiming deployment. The dashboard still uses the curated JSON dataset; it is not yet reading R2 health or changed documents. Missing source access, GitHub delays and stale checkpoints must be shown when the live status API is added.

Next: verify all configured endpoints and source reuse terms during the live run; add article discovery and structured extraction; expose a sanitized current health endpoint through a Worker bound to the private bucket. Keep unreviewed snapshots separate from the curated evidence register.

## Official implementation references

- https://developers.cloudflare.com/r2/examples/aws/boto3/
- https://developers.cloudflare.com/r2/api/tokens/
- https://developers.cloudflare.com/r2/api/s3/conditional-operations/
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
