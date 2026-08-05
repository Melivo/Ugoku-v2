# Task Board: offene Punkte Cleanup

Session: ultrawork-open-points-20260525

## P0
- [x] Fix `DEP0190` in `scripts/release.js` without suppressing warnings.
- [x] Add missing `## Entry Points` sections to runtime workflow files: `review.md`, `plan.md`, `debug.md`, `brainstorm.md`.
- [x] Align `.agents/results/plan-20260524-pros-api-bridges-non-hubspot.json` with Markdown task statuses.
- [x] Record decision that OS credential token storage is deferred to the next API-Bridge slice; no token exchange, refresh tokens, revocation, or `offline_access` now.
- [x] Verify with release dry-run, runtime validation, and relevant TypeScript checks.

## Scope Guard
- No real OAuth token exchange.
- No credential persistence implementation.
- No broad release script refactor beyond the child_process warning.
- No edits to `.agents/` SSOT files except reading workflow/rules; runtime files under `runtime/pros/.agents/` are release content and in scope.
