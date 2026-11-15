# Research protocol v0.1

## Aim

Test whether clearly defined indicators of institutional incentives and constraints improve predictions of publicly observable decisions relative to simple baselines. **No automated inference of criminality.**

## Unit of analysis

A specific institution–decision–time-window tuple. Example: a regulator's public decision on a specified restructuring proposal by a deadline. Avoid ambiguous outcomes such as "corruption gets worse".

## Evidence hierarchy

1. Primary contemporaneous documents: formal decisions, filings, dated regulatory reports, official releases.
2. Parliamentary testimony and oversight reporting, distinguished from legally established findings.
3. Credible independent reporting, with named attribution.
4. Analyst interpretation, labelled explicitly and kept separate from observations.

Every record must have a stable ID, title, publisher, published date, source URL and classification. Events must be supported by at least one source ID.

## Forecast protocol

1. Write the question and resolution rules *before* reading later evidence.
2. Set `created_at` (UTC), `close_at` (UTC) and an independent `resolve_by` date.
3. State numerical probability only if there is a defensible rationale; otherwise keep it `null` and label as a draft hypothesis.
4. Describe a baseline comparator (historical frequency, naive persistence or public market consensus where relevant).
5. Archive forecast as versioned file; **never edit locked forecast probability after closing**. Revisions must be distinct new forecast IDs and acknowledge the earlier version.
6. An outcome must be `true`, `false`, or `unresolved`; link to the decision/source establishing it.
7. Compute Brier score only for properly resolved 0/1 outcomes; show N and uncertainty, not just an average.

**Guard against leakage:** documents published after `created_at` cannot be treated as forecast inputs. Preserve both date of the event and date first observed, and account for retroactive edits.

## Candidate indicators (not a validated model)

- Financial constraint: debt maturity proximity, funding runway, capital adequacy.
- Regulatory pressure: penalties, enforcement milestones, binding compliance obligations.
- Political scrutiny: hearings, committee recommendations, ministerial statements.
- Negotiation leverage: public stakeholder statements, explicit decision dependencies, concentration of control.

Indicator definitions and transformation must be fixed in advance. Avoid subjective weighted "corruption risk" scores. Negative controls and rival explanations are mandatory.

## Validation plan

- MVP: structured case narrative and 1–3 *preregistered* binary forecasts; accuracy not meaningfully estimable.
- Later: multi-institution historical sample, naive and simple regression baselines, rolling-origin validation, class imbalance checks, and source-level audit.
- Calibration diagrams and Brier scores only after adequate resolved outcome sample; never assert forecast skill from anecdotal wins.

## Safeguards

- Distinguish allegation, parliamentary concern, verified finding, and inference.
- Avoid personal profiles, undisclosed personal data, and unsubstantiated allegations against named people.
- Attribution, correction log, and reproducibility instructions visible to readers.
- A substantive prediction about wrongdoing requires especially careful independent verification; platform should focus on observable institutional decisions rather than guilt inference.
