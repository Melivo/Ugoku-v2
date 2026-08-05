# QA Result - session-20260628-044806

Status: completed

## Scope

Read-only smoke test of configured non-HubSpot MCP servers. HubSpot excluded because it was already verified in the previous deterministic setup test.

## Readiness Matrix

| MCP server | Status | Evidence | Notes |
|---|---|---|---|
| codeberg-mcp | BLOCKED | `opencode mcp list`: `MCP error -32000: Connection closed` | Server configured but not connected. |
| gitea-mcp | PASS | `get_repo(leadt3ch/pro-select-harness)` returned repository metadata HTTP 200 | Read-only API call works. |
| serena | PASS | `read_memory`, `search_for_pattern`, `find_symbol` succeeded | Memory and code-analysis tools working after Desktop toggle restart. |
| pros-mcp-microsoft-graph | WARN | `graph_status`: `needs-credential` | Server reachable; Microsoft Graph credential missing from OS credential store. |
| pros-mcp-docx-local | PASS | Outside-workspace path rejected; workspace-local `docx_inspect` and `docx_extract` succeeded | Guard and read path both verified. |
| pros-mcp-office-files | PASS | Outside-workspace path rejected; workspace-local `pptx_inspect` and `pptx_extract` succeeded | Guard and read path both verified. Minimal fixture had slideCount 0 but tool responded ready. |
| pros-mcp-qnap-files | WARN | `qnap_status`: `needs-admin` / no profile configured | Server reachable; integration profile/admin setup missing. |

## Verification

- `bash .agents/skills/oma-orchestrator/scripts/verify.sh qa ...` failed because WSL `bash` could not find `node` for `oma`.
- Equivalent Windows-native command `oma verify qa --workspace C:\Users\visimeos\Projects\pro-select-harness` passed: 3 passed, 0 failed, 1 warning (`Charter Preflight` block missing from result).

## Files/Artifacts Created

- `.agents/results/plan-mcp-server-smoke-20260628.json`
- Workspace-local MCP smoke fixtures under `tmp/mcp-smoke-fixtures-20260628/`
- Temp outside-workspace guard fixtures under `C:\Users\visimeos\AppData\Local\Temp\opencode\mcp-smoke-fixtures-20260628`

## Acceptance Criteria

- Gitea MCP responds to read-only call: PASS
- Microsoft Graph MCP status clear: WARN needs credential
- QNAP MCP status clear: WARN needs profile/admin setup
- DOCX MCP guarded read: PASS
- Office/PPTX MCP guarded read: PASS
- Serena MCP smoke: PASS
- No credential/config mutation: PASS
