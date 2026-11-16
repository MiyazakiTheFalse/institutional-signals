# Official source access and recovery — November 2026

**Status:** Implemented alternative route discovery and safety checks. These are not a guarantee that a publisher will allow automated retrieval from GitHub-hosted runners.

## Known failures

The collector has repeatedly received HTTP 403 on the original `OFWAT-2026` page and original `PARL-2026-09`, `PARL-2026-10` and `PARL-2026-11` routes. For example, see the 16 November collection log in GitHub Actions. These are genuine retrieval failures and must remain visible.

A 403 must **not** be treated as a CAPTCHA or rate limit to defeat. The collector never uses credential guessing, rotating proxies, fabricated browser identities, unofficial replay services, or high-volume retries.

## Verified official discovery surfaces

| New source ID | Official route | Content scope | Forecast evidence? |
| --- | --- | --- | --- |
| `PARL-REPORT-PDF-API` | UK Parliament Committees API, `/api/Publications/55076/Standard/OriginalFormat` | Original-format report **candidate**, accepted only when response passes PDF signature and MIME validation | Only after a reviewer confirms it is the correct full report and records evidence provenance |
| `PARL-EFRA-PUBLICATIONS` | Committee's official publications index | Publication discovery only | No; not a substitute for original report or news text |
| `OFWAT-REPORT-PUBLICATION` | Ofwat's publication record for 2025–26 operational performance | Report download landing page | No; landing page is not report bytes |
| `OFWAT-DATA-PUBLICATION` | Ofwat's official open-data machine-readable-format publication record | Dataset download landing page | No; not the dataset itself |
| `OFWAT-DATA-DICTIONARY` | Ofwat's corresponding official dictionary publication record | Metadata/dictionary landing page | No; not the underlying dataset |

The UK Parliament publishes a supported Committees API; the exact report-document operation must still succeed on the runner and be reviewed before equivalence is established. Ofwat has distinct report, open-data and dictionary publication records. Each is separately monitored and labelled by scope. Do not promote an alternative because its URL *looks* related.

## Implemented safeguards

- Explicit, allowlisted source host and publication-document operation. The document adapter requests PDF and rejects HTML challenges, other binary formats and a mismatching document URL.
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
