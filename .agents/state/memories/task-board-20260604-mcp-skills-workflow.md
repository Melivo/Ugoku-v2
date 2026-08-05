# Task Board - MCP Skills/Workflow Update

Session: session-ultrawork-20260604-mcp-skills-workflow
Plan: docs/plans/work/016-opencode-desktop-mcp-setup.md

## Tasks

- [x] Update install-mcp-server-pros with Remote OAuth MCP classification.
- [x] Update mcp-config-sync-pros with OpenCode Remote OAuth MCP setup rules.
- [x] Decide whether to implement a HubSpot helper script: no helper, documented decision.
- [x] Update werkzeuge-mcp-einrichtung with HubSpot/OpenCode branch, consent gates, and needs-* states.
- [x] Update windows-runtime.md with Desktop OAuth/log/restart/auth-store details.
- [x] Document rotation and reauth path.
- [x] Verify packaging/runtime inclusion and run feasible checks.

## Gates

- PLAN_GATE: passed
- IMPL_GATE: passed for implemented docs/runtime artifacts
- VERIFY_GATE: passed after QA remediation
- REFINE_GATE: passed
- SHIP_GATE: passed; final external OAuth E2E remains manual

## Residual

- Full HubSpot/OpenCode OAuth E2E requires end-user OAuth and secret/env consent.
