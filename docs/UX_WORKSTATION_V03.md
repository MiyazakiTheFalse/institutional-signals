# Workstation UX v0.3 — acceptance contract

## Goal

Make the research experience useful **before** any operator uploads evidence or connects a cloud workspace. Present documented research first, with clearly signposted uncertainty. A user should be able to discover sources, events, connections and the absence of registered forecasts without configuring secrets.

## Implemented navigation

- **Overview:** case, current evidence caveats, four plain-language entry points, source/observation/graph counts and recent curated observations.
- **Timeline:** searchable dated observations linked to the curated source register.
- **Relationships:** interactive, accessible node selection; temporal evidence cutoff; search, scoped graph links, and inspectable provenance.
- **Evidence:** searchable source register, typed missing evidence requests and optional local import.
- **Forecasts:** explicit empty state; no invented probabilities, skill scores or model promises.
- **Workspace:** private authenticated collection status, local quarantine and reviewer submission. This is an operator tool, not required for public browsing.

## Truthfulness and UX rules

1. The bundled dashboard is labelled **curated and static** as of its data-export date.
2. Cloud source health must be labelled **collection health**, not document verification or predictive readiness.
3. Network edges require a verified review state, known provenance, and publication/first-observation/recording/review timestamps before the selected UTC cutoff. Invalid or superseded edges are not displayed as current.
4. The first graph contains **publisher attribution** only. Missing links do not imply missing real-world relationships, nor do publication links imply private knowledge or influence.
5. An empty forecast register displays an explanation rather than fake chart data.
6. There must be a keyboard alternative to clicking the graph: entity picker, search results and detail cards.
7. The workspace remains optional to read the research; imports and cloud submission have explicit separate steps.
8. No extra metered API, paid runner, new JavaScript package or unnecessary telemetry is introduced.

## Acceptance checks

- [ ] `npm ci && npm run build` passes with strict TypeScript.
- [ ] Python data export and repository tests pass.
- [ ] Verify initial Overview load on Windows, Linux and macOS packaged builds.
- [ ] Keyboard-only navigation: skip link, top navigation, entity picker, timeline and source search, evidence expansion and forecast empty state.
- [ ] At 320 px width, navigation and graph pan horizontally without clipping the rest of the page. Check at 760 px and desktop.
- [ ] Verify keyboard focus, reduced-motion handling, zoom to 200%, screen reader names and contrast.
- [ ] Select 15 November 2026: the four curated publication edges must not appear in historical replay because they were reviewed on 16 November.
- [ ] Select 16 November 2026 or later: the four publisher-attribution links should appear with timestamps and source references.
- [ ] Without a cloud connection, users can read the bundled dataset, while all live claims remain explicitly unverified.
- [ ] With an unavailable cloud connection, imports remain available locally and failed requests do not falsely display fresh status.
- [ ] User testing: a new participant can answer "What changed?", "Who published it?", "What is missing?" and "What can we predict?" without operator guidance.

## Remaining scope

This UX revision improves navigation and inspection but **does not** complete source extraction, human verified graph promotion, predictive calibration, live deployment, native signing, commercial billing or market validation. The research source registry is still initially small and static.

For production, complete native device tests, source-access work, cloud integration, and formal forecast preregistration described in the repository's open delivery issues.
