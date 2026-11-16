# Official source access and recovery — November 2026

**Status (16 November 2026):** The official Parliament API document operations are verified retrievable from the standard GitHub runner (HTTP 200; a 415,526-byte decoded PDF), but the downloaded contents remain **unreviewed**. Original Parliament/Ofwat HTML pages still return 403. Ofwat's complete machine-readable dataset remains unavailable to the collector.

## Known failures

The collector has repeatedly received HTTP 403 on the original `OFWAT-2026` page and original `PARL-2026-09`, `PARL-2026-10` and `PARL-2026-11` routes. For example, see the 16 November collection log in GitHub Actions. These are genuine retrieval failures and must remain visible.

A 403 must **not** be treated as a CAPTCHA or rate limit to defeat. The collector never uses credential guessing, rotating proxies, fabricated browser identities, unofficial replay services, or high-volume retries.

## Verified official discovery surfaces

| New source ID | Official route | Content scope | Forecast evidence? |
| --- | --- | --- | --- |
| `PARL-REPORT-PDF-API` | UK Parliament Committees API, `/api/Publications/55076/Document/305807/OriginalFormat` | Original-format report **candidate**; official JSON base64 PDF envelope decoded with strict schema, signature and size validation | Only after a reviewer confirms that the 415,526-byte document is the correct full report and records evidence provenance |
| `PARL-REPORT-PDF-FORMAT` | UK Parliament Committees API, `/api/Publications/55076/Standard/pdf` | Alternate official format-based request for the same publication; retrieved candidate, not independent evidence | Same review requirement; deduplicate using underlying primary document identity |
| `PARL-EFRA-PUBLICATIONS` | Committee's official publications index | Publication discovery only | No; not a substitute for original report or news text |
| `OFWAT-REPORT-PUBLICATION` | Ofwat's publication record for 2025–26 operational performance | Report download landing page | No; landing page is not report bytes |
| `OFWAT-DATA-PUBLICATION` | Ofwat's official open-data machine-readable-format publication record | Dataset download landing page | No; not the dataset itself |
| `OFWAT-DATA-DICTIONARY` | Ofwat's corresponding official dictionary publication record | Metadata/dictionary landing page | No; not the underlying dataset |

The Committees API publication metadata identifies document 305807 and filename *HC 664 - Amended The future of Thames Water-online.pdf*. Both documented PDF operations succeeded in a standard runner probe after decoding a JSON envelope whose `data` field contains base64-encoded PDF bytes. Format success does **not** automatically establish document contents or future predictive relevance. Ofwat has distinct report, open-data and dictionary publication records. Each is separately monitored and labelled by scope. Do not promote an alternative because its URL *looks* related.

## Implemented safeguards

- Explicit, allowlisted source host and publication-document operation. The document adapter accepts either raw PDF or the **official JSON base64 PDF envelope** with strict decoding, signature, MIME and size checks. HTML challenges, malformed base64, unrelated JSON and mismatched document URLs are rejected.
- Exactly one request per source per diagnostics run; no brute-force retry loops.
- Access-denied responses (401/403) cause at least 24 hours' collection backoff.
- Supplemental discovery routes remain optional for *source-health coverage*; their success cannot mark an original 403 route healthy.
- An original full-report requirement can accept the original Parliament API format only **after** its exact document has been independently reviewed and registered with the required capability.
- An Ofwat report, summary or landing page cannot satisfy the comparable operational-data requirement merely because the PDF/page is accessible.
- A new/updated document remains an unreviewed source snapshot until its content, provenance and relevance have been checked.
- The official route probe uses the same transport and format rules as collection rather than treating PDF downloads as JSON.

## Operational next steps

1. Run **Actions → Verify official source alternatives → Run workflow** on `main`. Each route is checked once with a clear retrieval vs blocked result; this is not an automatic forecast gate.
2. Review results: find which exact full reports/data files can be downloaded. Check publisher reuse terms, format, coverage, report ID, data dictionary and version.
3. Where the original server continues returning 403, seek an authorised machine API, obtain publisher permission, or use the scanned, operator-assisted evidence intake. A publisher may limit automated access independently of whether a URL is public to browsers.
4. For verified alternate documents, record reviewer-approved source hash and data capability. Without that, forecasts remain **on hold**.
5. For primary Ofwat machine-readable data, obtain a stable documented download URL and verify XLSX/CSV content; only then add an essential-capability route. A landing page alone is not enough.
6. After approval, verify end-to-end R2 storage and desktop coverage status. Enforce the existing no-paid-infrastructure constraint.

## References

- UK Parliament developer hub: https://developer.parliament.uk/
- Committees API operations: https://committees-api.parliament.uk/index.html
- EFRA publications index: https://committees.parliament.uk/committee/52/environment-food-and-rural-affairs-committee/publications/
- Ofwat operational report: https://www.ofwat.gov.uk/publication/water-company-operational-performance-report-2025-26/
- Ofwat machine-readable data: https://www.ofwat.gov.uk/publication/data-for-the-water-company-operational-performance-report-2025-26-open-data-friendly-machine-readable-format/
- Ofwat data dictionary: https://www.ofwat.gov.uk/publication/data-for-the-water-company-operational-performance-report-2025-26-open-data-data-dictionary/
