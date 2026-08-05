# Serena MCP Config Drift - 2026-06-29

## Symptom

- Serena MCP calls in OpenCode sessions timed out or aborted, including `search_for_pattern`, `read_memory`, `write_memory`, and `edit_memory`.
- OpenCode Desktop recovery sometimes required toggling the Serena MCP server off and on.
- `opencode mcp list` could show Serena connected, while agent-local MCP templates still contained stale Serena startup commands.

## Root Cause

The active SSOT at `C:/Users/visimeos/.config/mcp/servers.yaml` was already correct, but agent-local MCP templates had drifted:

- `C:/Users/visimeos/.agents/mcp.json` used the removed global Python path `C:/Users/visimeos/AppData/Local/Programs/Python/Python312/Scripts/serena.exe`.
- `C:/Users/visimeos/.agents/mcp_config.json` used `command: "serena"` with `--context antigravity` for a generic/OpenCode path and no timeout.
- `C:/Users/visimeos/Projects/pro-select-harness/.agents/mcp.json` used the removed global Python path.
- `C:/Users/visimeos/Projects/pro-select-harness/.agents/mcp_config.json` used `command: "serena"` with `--context antigravity` and no timeout.

The stale templates could reintroduce bad Serena startup behavior after reinstall/sync/copy operations. Broad or parallel Serena calls acted as a trigger for timeouts, but the durable fix was to remove the stale config shapes.

## Fix Applied

Updated all affected agent-local Serena MCP entries to the local `uv tool` executable and OpenCode/generic IDE context:

```text
C:/Users/visimeos/.local/bin/serena.exe start-mcp-server --context=ide --project-from-cwd
timeout: 60000
SERENA_LOG_LEVEL=info
```

Files changed:

- `C:/Users/visimeos/.agents/mcp.json`
- `C:/Users/visimeos/.agents/mcp_config.json`
- `C:/Users/visimeos/Projects/pro-select-harness/.agents/mcp.json`
- `C:/Users/visimeos/Projects/pro-select-harness/.agents/mcp_config.json`
- `C:/Users/visimeos/.agents/tests/serena-mcp-config-drift.ps1`

The normal MCP sync was also run:

```powershell
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\sync-mcp-config.ps1"
```

It synced OpenCode from `servers.yaml`; Codex, Claude, and Hermes were skipped because their client configs were not active in this host context.

## Regression Test

Added:

```text
C:/Users/visimeos/.agents/tests/serena-mcp-config-drift.ps1
```

The test validates:

- Home `.agents/mcp.json` and `.agents/mcp_config.json`.
- Project `.agents/mcp.json` and `.agents/mcp_config.json`.
- Home `.opencode/*.json*` files requested by the user.
- Project `.opencode/*.json*` files requested by the user.
- Serena command equals `C:/Users/visimeos/.local/bin/serena.exe`.
- Serena args include `start-mcp-server`, `--context=ide`, and `--project-from-cwd`.
- Stale `--context antigravity`, `--project .`, old global Python path, and missing timeout fail the test.

Verification result:

```text
Serena MCP config drift check passed.
Serena 1.5.3
opencode mcp list: serena connected via C:/Users/visimeos/.local/bin/serena.exe start-mcp-server --context=ide --project-from-cwd
```

## Similar Patterns Found

A native OpenCode `debug-investigator` scan covered:

- `C:/Users/visimeos/.agents`
- `C:/Users/visimeos/.opencode`
- `C:/Users/visimeos/Projects/pro-select-harness/.agents`
- `C:/Users/visimeos/Projects/pro-select-harness/.opencode`
- `C:/Users/visimeos/Projects/pro-select-harness/runtime/pros/.agents/skills`
- `C:/Users/visimeos/Projects/pro-select-harness/runtime/pros/.agents/workflows`

No additional active stale Serena MCP configs were found.

Benign remaining mentions are documentation warnings, historical bug/recap artifacts, and the regression test itself.

No `mcp_config.json` or `mcp*.json*` files were found under the Home `.opencode` or project `.opencode` directories.

## Residual Risk

- Historical result artifacts still mention older working paths; they are not active config, but future readers should avoid copying them.
- If a currently running OpenCode Desktop MCP process was started before this fix, it may need a UI-level Serena off/on toggle or OpenCode restart to pick up the repaired config.
