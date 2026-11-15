# Architecture decision records

Create a new numbered markdown file when changing architectural boundaries, persistent schemas, forecasting methods, security assumptions, runtime infrastructure or core dependencies.

Use this short format:

```md
# ADR-NNNN: Decision title
Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD

## Context
What problem and constraints force a decision?

## Decision
What are we doing, and what are the interfaces/invariants?

## Alternatives
What credible options were rejected and why?

## Consequences
Cost, failure modes, maintainability, privacy and security.

## Reversal plan
What evidence would make us reverse this decision and how?
```

Numbering is chronological; do not rewrite historical ADRs after acceptance. Supersede with a new ADR.
