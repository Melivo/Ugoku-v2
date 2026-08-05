# Work Progress

- Session: E2E pros installation test
- Current workflow step: Step 5 Monitor / guided execution
- Current test phase: Phase 2 Installation
- Phase 1 Preflight result: WARN. Node v24.16.0 and npm 11.13.0 present; existing `pros.ps1` found in AppData Roaming npm; `opencode.exe` found via WinGet Links and user notes Desktop install under AppData Local Programs OpenCode; AnythingLLM plugins path missing; user MCP config path exists.
- Phase 2 partial result: FAIL/WARN remediation. `npm run build` passed and `npm pack --workspace @pro-select/pros-cli` produced `pro-select-pros-cli-0.5.2.tgz`. `npm install -g .\pro-select-pros-cli-*.tgz` failed because PowerShell passed the wildcard literally to npm.
- Status: awaiting retry with exact tarball filename.
- Safety: no secrets requested; Phase 2 modifies global npm package installation.


## Phase 2 Result

- Result: PASS after remediation.
- `npm install -g .\pro-select-pros-cli-0.5.2.tgz` succeeded.
- `pros` and all four `pros-mcp-*` binaries are on PATH.
- `pros --help` succeeded.
- Remediation applied: updated `docs/plans/work/013-e2e-pros-installation-test.md` to use the exact tarball filename and document PowerShell wildcard behavior.

## Phase 3 Status

- Current test phase: Fallordnerinitialisierung.
- Awaiting user feedback.
- Safety: no secrets requested; writes only to a fresh case folder outside the source repo.


## Phase 3 Result

- Result: PASS.
- Case folder: `C:\Users\visimeos\Desktop\pros-e2e-test-case`.
- `pros init` initialized pros 0.5.2, release `pros-v0.5.2`, files installed: 242.
- `pros doctor` returned `Status: safe_to_continue`; all checks passed.

## Phase 4 Status

- Current test phase: Runtime-Inhalt pruefen.
- Awaiting user feedback.
- Safety: read-only inspection commands in the case folder.


## Phase 4 Result

- Result: FAIL.
- `pros-runtime-manifest.md`: missing (`Test-Path` returned False).
- `.agents/workflows/werkzeuge-mcp-einrichtung.md`: present.
- `pros-Hilfe`: present.
- Directory contents include `.agents`, `.claude-plugin`, `.pros`, `.serena`, `pros-Hilfe`, `AGENTS.md`.
- Root cause: `pros init` used configured Gitea auth and installed remote release `pros-v0.5.2`; that release bundle appears stale relative to local source changes and does not include `pros-runtime-manifest.md` even though local CLI install entries expect it.
- Remediation applied: updated test plan to document that local CLI tarball installation does not imply local runtime changes are installed when `pros init` uses remote release assets.
- Next decision needed: continue testing released end-user path or switch to local-dev runtime init for unpublished changes.


## Phase 4 Remediation Decision

- User chose Option 1: test unpublished local runtime changes.
- Plan updated with local dev retry commands using temporary empty `PROS_AUTH_DIR` and `pros --workspace <case> --force init` from the source repo.
- Awaiting user feedback for local-dev Phase 3/4 retry.


## Local Dev Doctor Remediation

- Local dev retry exposed a CLI bug: `initLocal` wrote `.pros/config.json` but not `.pros/state.json`; `pros doctor` requires `.pros/state.json` and reported `repair_needed`.
- Fix applied: `packages/pros-cli/src/init.ts` now writes local dev installer state with `installedVersion: dev`.
- Regression test added: `packages/pros-cli/src/cli.test.ts` verifies local dev init writes state.
- Verification: `npm test -- packages/pros-cli/src/cli.test.ts` passed; `npm run typecheck` passed.
- Awaiting user reinstall of local CLI tarball and local dev retry.


## Local Dev Retry Final Result

- Result: PASS.
- Reinstalled final local CLI tarball globally after fixes.
- Fresh local folder `pros-e2e-test-case-local-2`: `pros doctor` returned `safe_to_continue`; `.pros/state.json`, `pros-runtime-manifest.md`, workflow, and `pros-Hilfe` all present.
- Existing folder `pros-e2e-test-case-local` force retry now succeeds; `pros doctor` returned `safe_to_continue`; core paths all present.
- Proceeding to Phase 5 global Tool-Skills.


## Phase 5 Result

- Result: WARN.
- `pros tools` found all global tool skills as `foreign-conflict` and skipped them because they are not pros-managed.
- Required paths `install-mcp-server` and `mcp-config-sync` exist under `%USERPROFILE%/.agents/skills`.
- `pros tools update --dry-run` reported the same foreign conflicts and no writes.
- Proceeding to Phase 6 API Bridge Preflight.


## Phase 6 Result

- Result: PASS/WARN.
- `pros integrations preflight` reported global profile path, case allowlist path, OS credential store only, and Pros Runtime Manifest MCP guidance.
- `pros integrations status`: Microsoft Graph `needs-client-id`; DOCX local `profile-ready`; Office and QNAP `manual-bridge-required`.
- `pros integrations profile list`: no global integration profiles configured.
- No secrets observed in output.
- Proceeding to Phase 7 MCP binary smoke-test.


## Phase 7 Result

- Result: PASS.
- `pros-mcp-docx-local`, `pros-mcp-office-files`, `pros-mcp-microsoft-graph`, and `pros-mcp-qnap-files` are available as npm PowerShell shims under AppData Roaming npm.
- Phase 8 requires explicit user consent before editing `%USERPROFILE%/.config/mcp/servers.yaml`.
