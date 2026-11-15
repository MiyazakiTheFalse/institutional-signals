# Resource register (verified 15 November 2026)

## A. Primary institutional evidence

| ID | Authority | Resource / link | Role in study | Access and caveat |
|---|---|---|---|---|
| PARL-2026-09 | UK Parliament EFRA Committee | [HC 664 - The future of Thames Water and special administration](https://publications.parliament.uk/pa/cm5902/cmselect/cmenvfru/664/report.html) | Creditor control, regulator decisions, alternative special administration, parliamentary recommendations | Public HTML; attribute, do not mechanically reproduce report wholesale |
| PARL-2026-11 | UK Parliament EFRA Committee | [4 November 2026 water reform update](https://committees.parliament.uk/committee/52/environment-food-and-rural-affairs-committee/news/218705/water-sector-reform-must-close-loopholes-on-pollution-reporting-and-let-ministers-wield-threat-of-special-administration/) | Scrutiny of proposed regulation and regulatory-capture safeguards | Public parliamentary reporting |
| TW-2026-11 | Thames Water | [9 November 2026 recapitalisation update](https://www.thameswater.co.uk/news/2026/nov/rp15-tsa-and-psl-announcement) | Company-stated process, dates, negotiations, creditor agreement | Primary company press release; *party statement*, not independent verification |
| OFWAT-2026 | Ofwat | [Water Company Operational Performance Report 2025-26](https://www.ofwat.gov.uk/regulated-companies/company-obligations/outcomes/water-company-operational-performance-report-wcopr-2025-26/) | Comparative performance metrics and data download links | Check dataset descriptions and applicable licence |
| OFWAT-HIST | Ofwat | [Historical performance](https://www.ofwat.gov.uk/regulated-companies/company-obligations/performance/) | Historic time series and measure definitions | Some definitions change; avoid incomparable longitudinal measures |
| GOV-WATER | Four water regulators / GOV.UK | [Joint water industry performance insights](https://www.gov.uk/government/publications/water-industry-performance-insights-joint-regulator-report) | Cross-regulator triangulation | Public report, 29 Oct 2026 |
| EA-RESOURCES | Environment Agency / GOV.UK | [Water resources 2025-26 analysis](https://www.gov.uk/government/publications/water-resources-2025-2026-analysis-of-the-water-industrys-annual-water-resources-performance/water-resources-2025-to-2026-analysis-of-the-water-industrys-annual-water-resources-performance) | Operational context | Annual measures and units can vary |

## B. Authoritative APIs and data catalogues

- **[UK Parliament Committees API](https://committees-api.parliament.uk/index.html)**: publications, inquiries, oral/written evidence endpoints. Can start without an application key; verify live endpoint behaviours before scheduled collection.
- **[Ofwat open, machine-readable 2025-26 dataset](https://www.ofwat.gov.uk/publication/data-for-the-water-company-operational-performance-report-2025-26-open-data-friendly-machine-readable-format/)** and **[data dictionary](https://www.ofwat.gov.uk/publication/data-for-the-water-company-operational-performance-report-2025-26-open-data-data-dictionary/)**: manual initial import; preserve originals, provenance and units.
- **[Companies House developer hub](https://developer.company-information.service.gov.uk/get-started/)**: company profiles, officers, filing history. Requires a user account and **API key**; do not put keys in GitHub or frontend. [Official authentication guidance](https://developer.company-information.service.gov.uk/authentication); [rate-limiting](https://developer.company-information.service.gov.uk/developer-guidelines/): 600 requests/5 min default.
- **[Parliament reports and responses](https://committees.parliament.uk/work/8765/reforming-the-water-sector/publications/reports-responses/)**: official updates relevant to unresolved parliamentary recommendations.

## C. Free development infrastructure

- [GitHub - creating a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository) and [GitHub Actions billing](https://docs.github.com/en/actions/concepts/billing-and-usage). Standard hosted Actions are free in public repos; private accounts receive plan-dependent monthly allowance. Avoid paid runners.
- [Cloudflare Pages Git integration](https://developers.cloudflare.com/pages/configuration/git-integration/), [Pages limits](https://developers.cloudflare.com/pages/platform/limits/). Free plan currently lists 500 builds per month and one concurrent build; verify before expanding. Public static sites do not require an application backend.
- [Python](https://www.python.org/), [Vite](https://vite.dev/), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/). Libraries are free; hosting terms are separate.
- Optional later: [DuckDB](https://duckdb.org/), [Pandas](https://pandas.pydata.org/), [scikit-learn](https://scikit-learn.org/), [Apache ECharts](https://echarts.apache.org/), [Cloudflare D1](https://developers.cloudflare.com/d1/platform/pricing/). These **are not dependencies of the minimal starter**.

## D. Research and governance references

- **[Brier (1950), Verification of forecasts expressed in terms of probability](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2)**. For binary probabilities, Brier score = mean squared error of forecast probability versus observed 0/1 outcome (lower is better).
- **[TRIPOD+AI reporting statement](https://www.tripod-statement.org/)**: useful reporting principles for predictive modelling, although developed for healthcare; not a claim that this study is clinically validated.
- **[UK Open Government Licence 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/)**: reuse is allowed for material expressly offered under this licence with attribution and other conditions. Do not presume all websites' content is OGL.
- [ICO UK GDPR overview](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/) for future collection of personal data; MVP should omit unnecessary personal profiles.

## E. Still required for production

1. Create GitHub `MiyazakiTheFalse/institutional-signals` repository and push this package; choose private until comfortable releasing evidence/identities.
2. Create Cloudflare account and connect repo for deployment (free plan).
3. Optional: create Companies House developer account and **store API key in GitHub Actions secrets only** after approving collection scope.
4. Establish a real forecast target, deadline, base rate, blind resolution criteria and independent reviewer.
5. Verify that each source may be downloaded/reused in the intended manner; default to links and small attributed summaries.
