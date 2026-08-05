# Bug: mcp-cred false OK when CredentialManager module fails

Date: 2026-07-04

## Symptom

Running:

```powershell
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\mcp-cred.ps1" set -Target gitea-mcp -UserName GITEA_TOKEN
```

printed:

```text
New-StoredCredential: Argument 'New-StoredCredential' is not recognized as a cmdlet: Could not load type 'System.Web.Security.Membership'
[OK] Credential stored: gitea-mcp
```

But the credential was not actually stored. `cmdkey /list:gitea-mcp` returned `* NONE *`, and `mcp-cred.ps1 status -Target gitea-mcp` stayed `[MISSING]`.

## Root Cause

`McpTokenResolver.psm1` depended on the external PowerShell `CredentialManager` module for `New-StoredCredential`. On this Windows host the module exports the cmdlet but fails at runtime because it cannot load `System.Web.Security.Membership`. `mcp-cred.ps1` then printed `[OK]` without independently verifying that the credential could be read back.

## Fix Applied

Active userhome skill:

- `%USERPROFILE%/.agents/skills/mcp-config-sync/scripts/McpTokenResolver.psm1`
- `%USERPROFILE%/.agents/skills/mcp-config-sync/scripts/mcp-cred.ps1`

Delivered Pros runtime copy:

- `runtime/pros/.agents/skills/mcp-config-sync-pros/scripts/McpTokenResolver.psm1`
- `runtime/pros/.agents/skills/mcp-config-sync-pros/scripts/mcp-cred.ps1`

Changes:

- Added native Windows Credential Manager API calls via `Advapi32.dll` (`CredWrite`, `CredRead`, `CredDelete`).
- Made native API the primary path for write/read/status/remove.
- Kept `CredentialManager` module read fallback only for compatibility.
- Added write-after-read verification in `Set-McpToken`.
- Added `mcp-cred.ps1 set` and `sync` verification before printing `[OK]`.

## Regression Test

`%USERPROFILE%/.agents/results/bugs/mcp-credential-manager-regression.ps1`

Result: passed.

The test writes a dummy probe credential, verifies status/read, removes it, and verifies removal.

Runtime copy was separately verified with a dummy probe credential via its `McpTokenResolver.psm1`.

## Similar Patterns Found

The same broken `New-StoredCredential` write pattern was found in the delivered Pros runtime copy and fixed there. Remaining `Get-StoredCredential` usage is fallback-only after native read fails.

## User Action Still Needed

The previously entered real `gitea-mcp` token was not stored and is not recoverable from the failed command. Re-run:

```powershell
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\mcp-cred.ps1" set -Target gitea-mcp -UserName GITEA_TOKEN
& "$env:USERPROFILE\.agents\skills\mcp-config-sync\scripts\mcp-cred.ps1" set -Target codeberg-mcp -UserName FORGEJOMCP_TOKEN
```
