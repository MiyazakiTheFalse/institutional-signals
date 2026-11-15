# Security policy

Institutional Signals handles third-party evidence and may operate with private workspace credentials. Report vulnerabilities responsibly.

## Reporting

If GitHub's **Private vulnerability reporting** feature is enabled for this repository, use **Security → Report a vulnerability**. Otherwise contact the repository maintainer through a non-public channel before disclosing details. Do not include exploit steps, personal evidence, secrets or live credentials in public GitHub issues.

Describe the affected version, impact, minimal reproduction using dummy data, and suggested mitigation. Please allow a reasonable opportunity for triage and remediation before coordinated public disclosure.

## Engineering safeguards

- Store credentials only in appropriate local/hosted secret stores, not source code or frontend bundles.
- Use minimum-permission tokens and isolate user-supplied evidence from published material.
- Treat URLs, documents and extracted statements as untrusted inputs.
- Review dependency updates, especially Electron, networking, parsers and actions.
- Prefer staged rollout and rollback over automatic publication of high-stakes interpretations.
- On suspected exposure: contain access, rotate affected secrets, preserve an incident timeline and document the corrective change.

## Support scope

There is no guaranteed security response SLA. This project is a research prototype, not a certified security or investigative service.
