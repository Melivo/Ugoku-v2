# Bug: gitea/codeberg MCP red after Windows migration

Date: 2026-07-04

## Symptom

OpenCode showed `gitea-mcp` and `codeberg-mcp` as red/failed with `MCP error -32000: Connection closed`.

## Root Cause

The OpenCode config had migrated MCP entries pointing at local runtime wrappers under `%LOCALAPPDATA%/mcp/servers/...`, but the migrated OS did not have those runtime directories or wrapper files. The expected Windows Credential Manager entries were also absent.

Confirmed missing before fix:

- `C:/Users/phili/AppData/Local/mcp/servers/gitea-mcp/scripts/run_stdio.ps1`
- `C:/Users/phili/AppData/Local/mcp/servers/codeberg-mcp/scripts/run_stdio.ps1`
- Credential Manager target `gitea-mcp`
- Credential Manager target `codeberg-mcp`

## Fix Applied

- Installed local Node runtimes:
  - `%LOCALAPPDATA%/mcp/servers/gitea-mcp` with `gitea-mcp@0.0.10`
  - `%LOCALAPPDATA%/mcp/servers/codeberg-mcp` with `forgejo-mcp@1.2.0`
- Added fail-fast PowerShell wrappers:
  - `%LOCALAPPDATA%/mcp/servers/gitea-mcp/scripts/run_stdio.ps1`
  - `%LOCALAPPDATA%/mcp/servers/codeberg-mcp/scripts/run_stdio.ps1`
- Added runtime credential docs:
  - `%LOCALAPPDATA%/mcp/servers/gitea-mcp/CREDENTIALS.md`
  - `%LOCALAPPDATA%/mcp/servers/codeberg-mcp/CREDENTIALS.md`
- Re-added both servers to `%USERPROFILE%/.config/mcp/servers.yaml`.
- Ran MCP config sync; OpenCode config synced successfully.

## Current Expected Status

Both servers can still appear red until tokens are created, but they now fail for the correct reason: missing credentials, not missing runtime files.

Set tokens with:

```powershell
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\mcp-cred.ps1" set -Target gitea-mcp -UserName GITEA_TOKEN
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\mcp-cred.ps1" set -Target codeberg-mcp -UserName FORGEJOMCP_TOKEN
```

## Regression Test

`%USERPROFILE%/.agents/results/bugs/gitea-codeberg-mcp-runtime-regression.ps1`

The test asserts:

- `servers.yaml` contains `gitea-mcp` and `codeberg-mcp`.
- Both wrapper files exist.
- Both Node runtime entry points exist.
- Without tokens, both wrappers fail with the explicit `Token missing ...` message.

Verification result: passed.

## Similar Patterns Found

- Repo scan found only documentation/artifact references to `run_stdio.ps1` and `%LOCALAPPDATA%/mcp/servers` besides this new test.
- Host OpenCode config now has only these two `%LOCALAPPDATA%/mcp/servers/.../run_stdio.ps1` entries, and both paths exist.

## Related Tooling Issues

- `mcpm ls -v` fails due to local Python package drift: installed `pydantic-core 2.47.0` is incompatible with current `pydantic`, which requires `2.46.4`.
- `oma state:emit` fails because the `oma` shim points at missing `C:\Users\phili\node_modules\oh-my-agent\bin\cli.js` after migration.
