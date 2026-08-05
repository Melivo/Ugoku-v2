# Serena Timeout / Worker Recovery

Date: 2026-07-01

## Symptom

Serena MCP calls in OpenCode Desktop timed out with `MCP error -32001: Request timed out`. Process inspection showed repeated Serena/Python workers and dashboard-related children. `opencode mcp list` reported Serena as connected, but live tool calls could still hang.

## Root Cause

The issue was caused by multiple additive process sources:

- Active OpenCode Desktop was launching Serena without a dashboard-disable flag, so Serena used global `web_dashboard: true` and started the dashboard.
- Some templates used `--open-web-dashboard false`, but that only prevents opening the dashboard; it does not disable the dashboard server. The durable flag is `--enable-web-dashboard false`.
- `.serena/project.yml` enabled `dart`, `terraform`, and `python` in addition to `typescript`, which started unnecessary LSP workers including Pyright/uvx Python processes.
- OpenCode Desktop can cache MCP command definitions; an MCP off/on toggle restarted Serena but did not immediately pick up changed command arguments. A full OpenCode Desktop restart may be required after config changes.
- Separately, broad Serena `search_for_pattern` calls can hit Serena's own `tool_timeout`; that is a query-scope issue, not necessarily transport failure.

## Fix Applied

- Updated Home and workspace Serena MCP/OpenCode config layers to include `--enable-web-dashboard false`:
  - `C:/Users/visimeos/.agents/mcp.json`
  - `C:/Users/visimeos/.agents/mcp_config.json`
  - `C:/Users/visimeos/.config/mcp/servers.yaml`
  - `C:/Users/visimeos/.config/mcp/generated/opencode-mcp.jsonc`
  - `C:/Users/visimeos/.config/opencode/opencode.jsonc`
  - `.agents/mcp.json`
  - `.agents/mcp_config.json`
- Reduced `.serena/project.yml` languages to `typescript` only.
- Added regression coverage in `tests/mcp-config.test.ts`.
- Added `AGENTS.md` troubleshooting references to:
  - `mem:global/debug/serena-timeout-process-worker-recovery-20260701`
  - `mem:debug/serena-timeout-process-worker-recovery-20260701`

## Regression Test

`npx vitest run tests/mcp-config.test.ts` passed with 2 tests.

## Verification

- `serena_initial_instructions` succeeded after OpenCode Desktop Serena toggle.
- `serena_list_memories(topic="debug")` succeeded after toggle.
- `opencode mcp list` shows Serena configured with `--enable-web-dashboard false`.
- After a full OpenCode Desktop restart, the live `serena.exe` process command line included `--enable-web-dashboard false`.
- Latest Serena log `C:/Users/visimeos/.serena/logs/2026-07-01/mcp_20260701-041824_17904.txt` shows no dashboard startup and exposes 21 tools instead of 22; `open_dashboard` is gone.
- Process tree after full restart no longer showed Serena dashboard/WebView children, Pyright, Dart, or Terraform LSP workers; only TypeScript language server remained.

## Residual Risk

OpenCode Desktop may cache MCP command definitions during a running desktop session. If the live process command line does not match repaired config files after an MCP off/on toggle, fully restart OpenCode Desktop.

## Similar Patterns

Scans across Home/workspace `.agents`, `~/.config/opencode`, `~/.config/mcp/generated`, and `~/.config/mcp/servers.yaml` found the intended `--enable-web-dashboard` entries and no remaining `--open-web-dashboard` entries in those active config layers.
