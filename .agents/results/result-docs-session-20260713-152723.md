## Status: completed

### Summary

Repaired the P0 HubSpot credential documentation/runtime workflow guidance. The runtime workflow now gives agents a complete copy/paste-safe PowerShell 7 block using masked `Read-Host` piped to `pros ... --client-secret-stdin`, explicitly says not to invent a second prompt, and describes direct stdin/TTY semantics as one secret line plus Enter. README no longer uses the rendering-sensitive `[System.Net.NetworkCredential]::new(...)` conversion.

### Files changed

- `README.md`
- `docs/CLI-MCP-COMMANDS.md`
- `docs/MCP-CREDENTIALS.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/auth-and-credentials.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/debugging.md`
- `.agents/results/progress-docs-session-20260713-152723.md`
- `.agents/results/result-docs-session-20260713-152723.md`

### Verification

- Read `task-board` via Serena memory; root `task-board.md` was absent.
- Focused static search checked `NetworkCredential`, escaped `\\[System`, `client-secret-stdin`, and `MaskInput` references in scoped docs/runtime workflow files.
- `oma docs verify --json` ran after edits. Result remains pre-existing repo drift: `brokenCount=344` (`file=339`, `script=5`). No new scoped HubSpot/NetworkCredential issue was identified by the focused checks.
- `git status --short` inspected; unrelated pre-existing modifications in root `.agents/`, `.opencode/`, `.serena/`, and other docs were not touched by this docs repair except the permitted `.agents/results/*` artifacts.

### Acceptance criteria checklist

- [x] Workflow does not falsely claim Pros prompts after Client ID or needs a second Enter.
- [x] Workflow supplies a complete masked PowerShell pipeline for HubSpot secret setup.
- [x] Direct stdin/TTY semantics are documented as one line/Enter, coordinated with backend behavior.
- [x] README removes `NetworkCredential` conversion and escaped-bracket risk.
- [x] `docs/MCP-CREDENTIALS.md` and `docs/CLI-MCP-COMMANDS.md` clarify bare vs masked flows.
- [x] Relevant runtime workflow resources were checked and minimally updated.
- [x] Secret safety preserved; no secrets introduced.
