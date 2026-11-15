# Evidence requests and input security

The collector evaluates `config/case_dependencies.json` against current source checks and the operator-controlled reviewed-evidence registry. It writes compressed case readiness and upload requests to `status/case-readiness.json.gz` and `status/upload-requests.json.gz` in private R2. Missing requirements produce a named document request, rationale, acceptable formats and size limit. Static dashboard cards show requirements only, not live R2 status.

Only current, explicitly reviewed content matching a requirement's capability and current content hash can satisfy the gate. Repeated copies sharing a primary document ID count once. Stale, changed, future or unreviewed evidence holds inference. No trained forecasting engine is deployed yet; the readiness gate is the contract that engine must consume. An uploaded document does not automatically satisfy it.

## Operator-assisted intake

```bash
python scripts/intake_upload.py report.pdf --request-id thames-water-restructuring:parliament-report --source-url https://publications.parliament.uk/pa/cm5902/cmselect/cmenvfru/664/report.html --published-at 2026-09-18T00:01:00Z --store r2
```

Intake resolves the request against trusted configuration, validates the cited URL and publication timestamp, limits bytes read, permits only PDF/UTF-8 CSV, checks signatures, rejects unsafe filenames and obvious active PDF content or CSV formulas, and writes UUID-named compressed quarantine objects plus a provenance manifest. The original filename is metadata only. User URLs are stored as citations and never fetched. Archives, Office files and executables are not accepted. Negative CSV values currently need operator handling because the conservative formula check also rejects leading minus signs.

All uploads remain `quarantined` and `not_scanned`. Signature/keyword checks do not guarantee a PDF is benign. No parsing, rendering, execution, automatic promotion or LLM instruction following occurs during intake. A future promotion service must scan files, verify the document and publication provenance, link an equivalent source route, and record reviewer identity and the reviewed capability before evidence can become eligible. Uploaded document text is untrusted data, never authority to run tools or change settings.

## Browser and deployment protections

React renders text without raw HTML insertion; external citations are HTTPS-only with credential-bearing URLs refused. Dataset collection bounds and selected shape checks reject malformed input. Cloudflare Pages `_headers` adds CSP, anti-framing, MIME-sniffing protection and restricted browser permissions. These headers apply after Pages deployment, not automatically to Vite development or other hosts.

There is no public upload endpoint. Before enabling one, implement authentication, per-case ownership and authorization, CSRF/origin checks, request/rate/storage quotas, malware scanning or content disarm, audit logs, private attachment downloads and safe error handling on the server. Client validation cannot replace those checks. Do not describe all user interactions as secured or audited until the deployed service and those boundaries have been tested.

References: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html and https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html
