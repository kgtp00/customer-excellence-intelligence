# Source integration — staging

## Status
- One manual-only GitHub Actions collection test is included.
- Collector attempts to retrieve **public GOV.UK/MHRA search metadata**.
- Retrieved items become unapproved candidates in a workflow artifact, **not** website content.
- This connection has NOT yet been tested successfully on GitHub Actions.
- Global pharmaceutical sources remain the primary editorial objective; this UK connector is only a controlled first technical integration.

## How to test
GitHub → Actions → Collection smoke test (manual only) → Run workflow.
Inspect the logs. If it succeeds, download the `govuk-review-candidates` artifact, inspect the records, and share the file for quality review.
If it fails, share the log output. Do not enable scheduled collection until it passes.

## Boundaries
No company credentials, confidential business data, full-text article copying, AI scoring or automatic publication. Article rights and evidence must be evaluated before any future public intelligence feed is activated.
