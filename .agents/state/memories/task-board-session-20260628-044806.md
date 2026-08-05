# Task Board - session-20260628-044806

Status: COMPLETED
Plan: `.agents/results/plan-mcp-server-smoke-20260628.json`
Runtime vendor: OpenCode
Target vendor for qa: OpenCode
Dispatch: Native OpenCode task tool is available; for this host-bound MCP smoke test the orchestrator executes direct MCP/status probes and records results.

Resolved agent models (model_preset + overrides)
| Agent | Vendor / Model |
|---|---|
| frontend | opencode / openai/gpt-5.5 |
| backend | opencode / openai/gpt-5.5 |
| mobile | opencode / openai/gpt-5.5 |
| pm | opencode / zai-coding-plan/glm-5.2 |
| qa | opencode / openai/gpt-5.5 |
| docs | opencode / openai/gpt-5.4-mini |
| orchestrator | opencode / openai/gpt-5.4 |

Tasks
| ID | Task | Agent | Priority | Status | Notes |
|---|---|---|---|---|---|
| 1 | Inventory configured MCP servers | qa | P0 | completed | OpenCode inventory captured; codeberg failed, gitea/serena/pros Graph/DOCX/Office/QNAP connected. |
| 2 | Run read-only smoke checks for API-backed MCP servers | qa | P0 | completed | Gitea PASS; Microsoft Graph reachable but needs-credential; QNAP reachable but needs-admin/profile. |
| 3 | Run guarded local-file MCP smoke checks | qa | P0 | completed | DOCX/PPTX PASS on workspace fixtures; outside-workspace guard rejection confirmed. |
| 4 | Run Serena MCP smoke check | qa | P0 | completed | Memory read, pattern search, and symbol search PASS. |
| 5 | Summarize MCP server readiness | qa | P1 | completed | Readiness matrix written to result memory. |

Context anxiety tracking
| Agent | Status | Note |
|---|---|---|
| qa | on-track | P0 complete within expected turns; no reset needed. |
