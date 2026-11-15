# Engineering guardrails — v1

## Intent

Keep the codebase inexpensive to change, reliable to audit, and safe to ship. Policy must be proportionate: small docs/UI edits stay easy; trust-boundary and forecasting changes require stronger evidence.

## Zero-paid-CI policy

**No paid GitHub testing, runner upgrades, or unapproved metered services.** This is a release requirement, not merely a cost preference.

- This repository is currently public; ordinary `ubuntu-latest`, `windows-latest`, and `macos-latest` jobs are standard runners and are free for public repositories under GitHub's current published terms. Do not choose larger or premium runners.
- If visibility changes to **private**, suspend automated installer builds until the owner verifies current free allowance and billing safeguards. Included private minutes are not an unlimited no-charge promise.
- Pull requests run the normal validation suite without packaging installers. Native packaging runs on demand, on version tags, or when desktop packaging files change on \`main\`. This avoids generating three installers for unrelated source edits.
- Keep build artifacts short-lived (one day), avoid unnecessary caches and repeated builds, and monitor storage usage; storage can be metered separately from compute.
- Configure a **hard GitHub Actions spending budget** at the account/repository billing level, with `Stop usage when budget limit is reached` where available, and enable usage alerts. Repository code cannot set or verify billing budgets.
- Never add a new paid integration, external API, premium GitHub feature, billing-enabled service, or paid runner without explicit owner authorization and a documented cost assessment.
- Provide a local test path that functions without GitHub Actions. Successful CI is verification, not a reason to incur charges.
- Re-check GitHub's actual billing terms and repository visibility before changing workflows.

## Merge requirements

1. Use branches and pull requests; do not use `main` as an experimentation area.
2. CI must execute the Python/data tests, JavaScript tests, TypeScript/Vite build, and repository hygiene check.
3. Do not merge red CI. Never describe unexecuted tests as passing.
4. New behaviour gets a regression test; repairs get a test that would have failed before the fix.
5. Architectural, schema, security or forecast-evaluation changes get an ADR under `docs/adr/`.
6. Prefer additive, versioned data changes. Design migration and rollback **before** changing durable formats.
7. Keep raw sources, analyst claims and reviewed facts separate. No silent upgrading of certainty.
8. Require dependency/security assessment for any new networked service, privileged operation, or package.
9. Publish a draft desktop release and inspect OS-specific artifacts before releasing to users.
10. Limit one active cross-cutting refactor at a time; document debt explicitly rather than hiding it in TODOs.

## Definition of done

- A user-visible outcome and acceptance criteria are stated.
- Tests include edge cases and relevant temporal/validation boundary conditions.
- Security, privacy, accessibility and operational failure modes are assessed at the appropriate risk tier.
- Public claims retain source and as-of provenance.
- No unexpected credentials, binary outputs or cache directories are added to Git.
- Relevant documentation and examples reflect the **actual** status.
- Rollback or disablement is feasible and documented.

## Known debt, tracked explicitly

| ID | Item | Impact | Closure gate |
|---|---|---|---|
| DEBT-001 | No committed npm lockfile | Installer builds are not deterministic | Commit generated lockfile, switch CI/release to `npm ci`, verify |
| DEBT-002 | Native installers not yet acceptance-tested | Installation may fail outside runners | Build + install/launch/uninstall test on each OS |
| DEBT-003 | No signed/notarised desktop packages | User trust and OS warnings | Review signing plan, sign and notarise production releases |
| DEBT-004 | Knowledge graph contains no verified real-world relationships | Decision map lacks validated connections | Add primary-sourced, reviewed edges with as-of tests |
| DEBT-005 | Live archive not connected to curated dashboard | Freshness cannot be represented as live | End-to-end source → review → publication with stale/error states |

## What automation does and does not enforce

The repository hygiene script detects tracked secrets/private-key markers, forbidden artifacts, merge conflicts and malformed policy files. CI enforces tests and a build. PR templates and ADR rules are **review conventions** until GitHub branch protection/rulesets make checks mandatory. A template alone cannot prove a reviewer completed the work.

Repository settings should require pull requests, passing checks and no force pushes to `main`. Those settings must be configured and verified by an administrator; this document does not claim they are active.

Quarterly: retire or re-prioritise debt entries based on actual usage, security exposure, failure frequency and cost to change.
