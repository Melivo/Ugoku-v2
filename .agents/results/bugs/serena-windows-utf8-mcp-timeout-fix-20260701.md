# Serena Windows UTF-8 MCP Timeout Fix - 2026-07-01

## Symptom

OpenCode Serena MCP calls timed out with `MCP error -32001: Request timed out`. `serena_write_memory`, `serena_read_memory`, and `serena_search_for_pattern` could fail after Serena had previously worked. After failed MCP calls, no surviving or responsive Serena MCP request path remained for the current operation.

## Environment

- Windows PowerShell / OpenCode.
- Serena installed with `uv tool install -p 3.13 serena-agent`.
- Local executable: `C:/Users/visimeos/.local/bin/serena.exe`.
- Serena version verified: `1.5.3`.

## Root Cause

Serena backend, LSP, and memory CLI were healthy, but Windows CP1252 stdio could not encode Serena Unicode status output. `serena project health-check` ran all tool checks successfully, then failed with `UnicodeEncodeError` while printing Unicode status characters. The same command passed when run with `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`.

OpenCode started the Serena MCP process without those environment variables, so the MCP server could terminate or stall during startup/output and surface as timeouts.

## Fix Applied

- Added non-secret UTF-8 environment to `%USERPROFILE%/.config/mcp/servers.yaml` under `serena.environment`:
  - `PYTHONIOENCODING: utf-8`
  - `PYTHONUTF8: "1"`
- Ran `%USERPROFILE%/.agents/skills/mcp-config-sync/scripts/sync-mcp-config.ps1`, which synced OpenCode.
- Restarted OpenCode so the active MCP process used the new config.
- Updated project MCP configs `.agents/mcp.json` and `.agents/mcp_config.json` with the same env vars.
- Updated `tests/mcp-config.test.ts` to assert both project MCP configs keep the Serena UTF-8 env.
- Updated local and runtime MCP sync guidance to document this Windows Serena requirement.

## Files Changed

- `%USERPROFILE%/.config/mcp/servers.yaml`
- `%USERPROFILE%/.config/mcp/generated/opencode-mcp.jsonc`
- `%USERPROFILE%/.config/opencode/opencode.jsonc`
- `%USERPROFILE%/.agents/skills/mcp-config-sync/SKILL.md`
- `.agents/mcp.json`
- `.agents/mcp_config.json`
- `tests/mcp-config.test.ts`
- `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md`
- `build/runtime-projection/.agents/skills/mcp-config-sync-pros/SKILL.md`

## Regression Test

- `tests/mcp-config.test.ts` now verifies both `.agents/mcp.json` and `.agents/mcp_config.json` include:
  - `PYTHONIOENCODING: utf-8`
  - `PYTHONUTF8: "1"`

## Verification

- `serena_initial_instructions` via MCP: PASS after OpenCode restart.
- `serena_write_memory debug/serena-mcp-timeout-mcp-smoke-20260701`: PASS.
- `opencode mcp list`: Serena connected.
- `python -m json.tool .agents/mcp.json` and `.agents/mcp_config.json`: PASS.
- `%USERPROFILE%/.config/mcp/servers.yaml` YAML parse: PASS.
- `npm test -- --run tests/mcp-config.test.ts`: PASS, 2/2 tests.

## Similar Patterns Found

- `.agents/mcp.json` and `.agents/mcp_config.json` had Serena entries without UTF-8 env; both fixed and covered by regression test.
- Runtime and generated MCP sync guidance lacked the UTF-8 note; both updated.
- Existing historical docs mention stale Python paths; not directly part of this fix.

## Residual Risk

Large `serena_write_memory` calls can still hit MCP request timeout or leave the current MCP operation queue unresponsive. Keep memory entries concise, or write large durable reports to `.agents/results/bugs/` and use Serena memory for concise summaries.

## Operational Note

If MCP calls still fail after config sync, fully restart OpenCode. MCP process definitions are loaded at client startup; syncing the JSON while OpenCode is running does not reliably replace the active Serena process environment.

## Follow-Up Timeout Hardening

After the UTF-8 fix, a large `write_memory` call could still wedge the long-lived OpenCode Serena MCP request queue while the Serena CLI backend remained healthy. To reduce false timeouts and make recovery deterministic, Serena is now configured with:

- OpenCode/client timeout: `180000` ms.
- Serena server arg: `--tool-timeout 180`.
- UTF-8 env retained: `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1`.
- Dashboard disabled: `--enable-web-dashboard false`.

Project guidance in `AGENTS.md` now says to use Serena MCP by default, but to use the local Serena CLI for Serena-only operations when MCP times out or the active queue appears wedged. If the stale `serena.exe start-mcp-server` process remains stuck, terminate it and fully restart OpenCode before resuming MCP-dependent workflows.
