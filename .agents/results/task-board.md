# Task Board — Ultrawork Session 20260628-064120

> Note: Serena memory store timed out; this is the filesystem-backed task board per memory-protocol.md file-based mode.

> Microsoft Graph OAuth Business Write (delegated, customer-facing OpenCode + AnythingLLM MCP).

**Session**: 20260628-064120
**Workflow**: ultrawork / ralph
**Phase**: PLAN (Steps 1-4 complete)
**Plan**: `.agents/results/plan-20260628-064120.json`
**Complexity**: Complex

## Active Constraints

- Delegated Microsoft user permissions only — no application-wide access.
- No direct send, no delete, no raw Graph passthrough tool.
- Attachments: allowlist (pdf, non-macro Office, ODF, txt/csv/tsv, png/jpg/jpeg/gif/webp) + MIME + size; deny archives/binaries/scripts/source/macro.
- If Graph semantics are unclear → read official Microsoft docs before guessing (T4/T5/T6/T11).
- No secrets in OpenCode/AnythingLLM client config.

## Tasks

| ID | Title | Agent | Pri | Status | Deps | Ralph |
|----|-------|-------|-----|--------|------|-------|
| 1 | Graph-MCP customer-facing naming | backend | P0 | TODO | — | C5 |
| 2 | OAuth scopes + status tier model | backend | P0 | TODO | 1 | C1 |
| 3 | Graph safety policy (allow/deny/confirm/targets) | backend | P0 | TODO | 2 | C2 |
| 4 | Calendar write functions (create/update/invite/shared/recurrence) | backend | P0 | TODO | 3 | C3 |
| 5 | Mail draft functions (create/update/shared mailbox) | backend | P0 | TODO | 3 | C4 |
| 6 | Draft attachment support (allowlist/MIME/size/deny) | backend | P0 | TODO | 5 | C4 |
| 7 | MCP tools (6 write tools + schemas + confirm gates, no send/delete/raw) | backend | P0 | TODO | 4,5,6 | C3,C4 |
| 8 | OpenCode/AnythingLLM config (command-only, no secrets) | backend | P1 | TODO | 1,7 | C5 |
| 9 | CLI/doctor/status UX (6 readiness states) | backend | P1 | TODO | 2,3 | C1 |
| 10 | Tests (policy/forbidden/confirm/draft-only/recurrence/attach/shared/readiness) | qa | P0 | TODO | 3-9 | C2-C5 |
| 11 | Microsoft docs research gate | backend | P1 | TODO | 4,5,6 | C3,C4 |
| 12 | README + runtime workflow (customer setup, allow/forbid) | docs | P1 | TODO | 7,8,9 | C6 |
| 13 | End-to-end smoke (OAuth/MCP status/safe flows/forbidden/client config) | qa | P1 | TODO | 10,12 | C6 |

## Parallelism

- A: [1] → B: [2,3] → C: [4,5,6] → D: [7] → E: [8,9] → F: [10,11] → G: [12,13]
- Critical path: T1→T2→T3→{T4‖T5→T6}→T7.

## Phase Status

- [x] PLAN Steps 1-4
- [ ] IMPL
- [ ] VERIFY
- [ ] REFINE
- [ ] SHIP
