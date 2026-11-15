# GitHub and free hosting setup

## Prerequisites

GitHub login: **MiyazakiTheFalse** (connected account verified 15 Nov 2026). Local Git and Node.js 20+ recommended; Python 3.11+.

## Create a new repository (one unavoidable user step)

The connected GitHub tool cannot create repositories. Go to [github.com/new](https://github.com/new) while signed in:

- Owner: `MiyazakiTheFalse`
- Repository: `institutional-signals`
- Description: `Evidence-backed institutional behaviour research and forecasting`
- Visibility: **Private to start**. Public later when ready; this does not change free-plan source code.
- Do not initialise README, .gitignore, or license: all are included here.

Extract the provided ZIP on your computer, open a terminal *inside* the `repository` directory, then:

```bash
git init
git branch -M main
git add .
git commit -m "Initial Institutional Signals research prototype"
git remote add origin https://github.com/MiyazakiTheFalse/institutional-signals.git
git push -u origin main
```

GitHub may request account authentication. Use GitHub Desktop instead if easier: `File > Add local repository`, choose extracted folder, create repository from it, then publish as private.

## Actions / CI

The repository contains `.github/workflows/ci.yml` (tests, data validation, dashboard build on pushes and pull requests) and `.github/workflows/data-refresh.yml` (weekly rebuild/validation). The weekly job does **not** scrape the internet or invent new records. Review Actions permissions before enabling; no secrets required for MVP.

## Cloudflare Pages (optional deployment)

1. Sign into Cloudflare dashboard, open **Workers & Pages** and create a **Pages** project.
2. Connect GitHub and select `MiyazakiTheFalse/institutional-signals`. If the repo is private, authorise access to it.
3. Framework preset `Vite`, production branch `main`, build command `npm run build`, output directory `dist`, root directory `/`.
4. Deploy; use the generated `*.pages.dev` URL. No custom domain is needed.

Static pages will show committed data at build time, not live query results. For automatic publishing of refreshed data later, use a reviewed PR/commit and Cloudflare's Git integration.

## Optional API phase

Companies House needs an API key. Create one in the official developer portal, then save it as a GitHub repository **Actions secret**, never as a tracked file or `VITE_*` variable (Vite browser variables are public). Implement a separate authenticated ingestion job before enabling that data source.

## Troubleshooting

- `npm install` fails: check Node.js version and network; `npm ci` is preferred after lockfile exists.
- `git push` fails because remote has commits: create a blank repository without a README and retry; do not force-push unrelated history.
- Cloudflare shows blank page: confirm build directory `dist` and inspect Pages build logs.
- GitHub Actions reports missing Python/node: verify runner images and versions in workflow YAML.
