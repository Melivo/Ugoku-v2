# Pros Windows Enduser Init/Auth Store Diagnosis

Date: 2026-07-04

## Symptom

An affected Windows end-user environment previously showed `pros init` failing with manifest verification errors such as missing `.agents/...` runtime files. During a later reset attempt, `pros auth token set --stdin` failed with:

```text
EPERM: operation not permitted, open 'C:\Users\SkylarFalcone\AppData\Local\pros\auth.json'
```

The private npm registry itself was reachable via:

```powershell
npm view @pro-select/pros-cli@latest --@pro-select:registry=https://git.leadt3ch.com/api/packages/leadt3ch/npm/
```

## Diagnosis

Code tracing found the `pros init` path is narrow:

- `cli.ts` dispatches `pros init` to `initWorkspace()`.
- `initWorkspace()` downloads `pros-runtime.apm`, `pros-runtime.apm.sha256`, and `pros-manifest.json` from the latest stable `pros-v*` release.
- The bundle is extracted via `zip.extract()`.
- `verifyManifest()` checks each manifest file path and reports `File missing: ...` if the extracted bundle does not contain that exact relative path.

A clean Windows sandbox install using an isolated npm prefix installed `@pro-select/pros-cli@0.5.25` from the private registry and successfully ran:

```text
Initialized pros 0.5.25
Release: pros-v0.5.25
Files installed: 197
```

A separate dual-boot Windows validation also confirmed:

- npm can read `@pro-select/pros-cli@0.5.25` from the private registry.
- sandbox install works.
- sandbox `pros init` works.
- global install works.
- global `pros init` works.
- `pros doctor` reports `safe_to_continue`.

## Root Cause

The npm package and `pros-v0.5.25` runtime release are not generally corrupt. The remaining likely cause is local state on the affected end-user machine, especially the Pros auth store under:

```text
%LOCALAPPDATA%\pros\auth.json
```

The observed `EPERM` confirms that `pros` cannot reliably write its auth file on that machine. Potential causes include stale file attributes, incorrect ownership/ACLs, a locked file, antivirus interference, or another local Windows profile issue.

The original manifest verification error should be re-tested only after the auth store is repaired and the path-resolved global `pros` installation is confirmed.

## Minimal Remediation

On the affected machine, repair local Pros auth state first:

```powershell
$authDir = Join-Path $env:LOCALAPPDATA "pros"
$authFile = Join-Path $authDir "auth.json"

attrib -h "$authDir" 2>$null
attrib -h "$authFile" 2>$null
Remove-Item -LiteralPath $authFile -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $authDir | Out-Null

$prosToken = Read-Host "pros release token" -MaskInput
$prosToken | pros auth token set --stdin
Remove-Variable prosToken
pros auth status
```

If `EPERM` persists, collect:

```powershell
$authDir = Join-Path $env:LOCALAPPDATA "pros"
Get-Item -LiteralPath $authDir -Force | Format-List *
icacls "$authDir"
Get-Command pros | Format-List -Property CommandType,Name,Source,Definition
npm list -g @pro-select/pros-cli --depth=0
```

## Files Changed

- `README.md`: clarified npm registry token configuration and separation from `pros auth`.

## Regression / Verification

No code fix was applied because the release and npm package are verified healthy. Verification was performed through clean Windows sandbox installs and global installs.

## Similar Patterns

`pros update` reuses `initWorkspace()`, so it would also be affected if a machine has broken auth state or a wrong PATH-resolved `pros` wrapper. No additional release-packaging defect was confirmed.
