# QA Review Result - Ultrawork VERIFY - Session 20260701-070312

## Status
completed

## Review Result: FAIL

VERIFY_GATE: **FAIL** — 0 CRITICAL, 3 HIGH, 2 MEDIUM, 1 LOW.

## Summary
Plan-21-Implementierung ist mechanisch baubar und die Testsuite laeuft durch, aber die VERIFY-Kriterien sind nicht erfuellt: Runtime-Manifest, Runtime-Workflow und committed Runtime-Projection enthalten weiterhin legacy `pros-mcp-*`/`office-files` Referenzen. Dadurch scheitern C1, C2, C6 und C7 zumindest teilweise. Keine verifizierten Security-CRITICALs; Excel Write-Gates, Backup, Workspace Guard, Macro-Deny und MCP-Redaction sind in Code/Tests vorhanden.

## Files changed by QA
- `.agents/results/progress-qa-reviewer-20260701-070312.md`
- `.agents/results/result-qa-reviewer-20260701-070312.md`

## Files reviewed
- Plan/Criteria: `.agents/results/plan-20260701-070312.json`, `.serena/memories/session-ralph-20260701-070312.md`
- Backend: `packages/pros-cli/package.json`, `packages/pros-cli/src/excel-local.ts`, `packages/pros-cli/src/mcp-excel-local.ts`, `packages/pros-cli/src/mcp-powerpoint-local.ts`, `packages/pros-cli/src/mcp-docx-local.ts`, `packages/pros-cli/src/mcp-client-config.ts`, `packages/pros-cli/src/integration-config.ts`, `packages/pros-cli/src/integration-registry.ts`, `packages/pros-cli/src/mcp-servers.test.ts`, `packages/pros-cli/src/excel-local.test.ts`, `packages/pros-cli/src/stale-name-guard.test.ts`
- Docs/Runtime: `runtime/pros/pros-runtime-manifest.md`, `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`, `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md`, `build/runtime-projection/pros-runtime-manifest.md`, `build/runtime-projection/.agents/skills/mcp-config-sync-pros/SKILL.md`, `docs/CLI-MCP-COMMANDS.md`, `docs/MCP-CREDENTIALS.md`, `docs/pros-hilfe-src/endnutzerhandbuch.md`
- Out-of-scope worktree risk: `.agents/mcp.json`, `.agents/mcp_config.json`, `AGENTS.md`, `.serena/project.yml`

## Commands / Evidence
- `serena_initial_instructions` — TIMEOUT; documented fallback used.
- `git status --short; git diff --stat; git diff --name-status` — many Plan-21 files changed plus out-of-scope root `.agents/*` changes.
- `npm run typecheck` — PASS.
- `npm run lint` — PASS, Biome checked 65 files, no fixes applied.
- `npm test` — PASS, 24 test files passed, 188 tests passed, 1 skipped.
- `npm run build` — PASS.
- `npm audit --audit-level=moderate` — PASS, 0 vulnerabilities.
- `npm run coverage` — PASS, All files line coverage 69.55%.
- Grep stale scans:
  - `Pros Office Files MCP|pros-mcp-office-files|Office Files MCP`: runtime source clean for exact phrase, but build projection has stale skill command at `build/runtime-projection/.agents/skills/mcp-config-sync-pros/SKILL.md:33`; docs historical plans also contain expected historical hits.
  - `pros-mcp-(docx-local|microsoft-graph|office-files|powerpoint-local)`: user-facing runtime hits remain at `runtime/pros/pros-runtime-manifest.md:57`, `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md:72-73`, and build projection equivalents.
  - `\boffice-files\b`: stale current runtime/projection hits remain at `runtime/pros/pros-runtime-manifest.md:75` and `build/runtime-projection/pros-runtime-manifest.md:75`.

### CRITICAL
- None.

### HIGH
- `runtime/pros/pros-runtime-manifest.md:57` and `build/runtime-projection/pros-runtime-manifest.md:57` — The delivered runtime still lists Microsoft Graph with legacy command `pros-mcp-microsoft-graph`, while lines 59 already list the canonical `mcp-microsoft-graph`. This duplicates the same target and can make end-user setup follow a non-existent/retired command, failing C2/T8/C6. Evidence: grep scan for `pros-mcp-(docx-local|microsoft-graph|office-files|powerpoint-local)` returned these lines; `packages/pros-cli/package.json:9` exposes only `mcp-microsoft-graph`. Remediation:
  ```md
  <!-- remove the stale duplicate row entirely, keep only the canonical row -->
  | Microsoft Graph | First-party `@pro-select/pros-cli` binary | stdio | Command `mcp-microsoft-graph`; optional args `--profile <profileId>` | Delegated Microsoft OAuth token in OS Credential Store only; no application permissions | Read tools plus confirmed safe writes: calendar create/update/invite and mail-draft create/update/allowed attachments | No direct send, mail delete, calendar delete, raw Graph payloads, mail bodies, attendee disclosure in read outputs, or token material in tool output |
  ```

- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md:72` and `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md:73` — End-user workflow still instructs AnythingLLM/OpenCode to use `pros-mcp-microsoft-graph` and calls it a compatibility command, directly contradicting Plan T2/T8 and criterion C2 (no Office compatibility alias bins). Remediation:
  ```md
  Microsoft Graph wird als `microsoft-graph` mit `command: mcp-microsoft-graph`, `args: []` eingetragen.
  ... Microsoft Graph nutzt den kanonischen Servernamen `microsoft-graph` und den lokalen Befehl `mcp-microsoft-graph`.
  ```

- `build/runtime-projection/.agents/skills/mcp-config-sync-pros/SKILL.md:33` — Committed projection artifact still lists `pros-mcp-microsoft-graph`, `pros-mcp-docx-local`, and `pros-mcp-office-files` and omits `mcp-excel-local`, while `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md:33` is corrected. This means the checked-in projection is stale and T8's “Runtime-Manifest und Projection synchronisiert” claim is false. Remediation:
  ```md
  Expected commands are `mcp-microsoft-graph`, `mcp-docx-local`, `mcp-powerpoint-local`, `mcp-excel-local`, and `pros-mcp-qnap-assistant`; workspace-scoped file servers should pass `--workspace <case-folder>` and provider-backed servers may pass `--profile <profileId>`.
  ```

### MEDIUM
- `runtime/pros/pros-runtime-manifest.md:75` and `build/runtime-projection/pros-runtime-manifest.md:75` — API Bridge table still exposes `Office files` / provider ID `office-files` for current runtime documentation. This fails T5/T8 and C1/C6 because PowerPoint-specific naming and `powerpoint-local`/`excel-local` provider IDs are supposed to replace the generic office-files wording. Remediation:
  ```md
  | Local PowerPoint | `powerpoint-local` | `api-bridge-readiness` | No credential required | PPTX inspect/extract, text preview |
  | Local Excel | `excel-local` | `api-bridge-readiness` | No credential required | XLSX/XLSM inspect/extract/range read, preview edit, confirmed XLSX write with backup |
  ```

- `packages/pros-cli/src/stale-name-guard.test.ts:29` — The stale-name regression test only scans `packages/pros-cli/src`, `packages/pros-cli/package.json`, and `package-lock.json`; it does not scan `runtime/pros`, `build/runtime-projection`, or target docs. `npm test` therefore passes while stale user-facing runtime/projection references remain, failing C7’s detection intent. Remediation:
  ```ts
  const files = [
    ...(await collectFiles(sourceRoot)),
    ...(await collectFiles(path.join(repoRoot, "runtime", "pros"), [".md"])),
    ...(await collectFiles(path.join(repoRoot, "build", "runtime-projection"), [".md"])),
    ...packageFiles,
  ].filter((filePath) => !filePath.endsWith("stale-name-guard.test.ts"));
  ```
  Also allowlist historical `docs/plans/**` deliberately, or scan only the current target docs from T8.

### LOW
- `.agents/mcp.json:13` and `.agents/mcp_config.json:20` — Root `.agents/` SSOT files are modified with a hard-coded user-local Serena path (`C:/Users/visimeos/.local/bin/serena.exe`). This is outside Plan 21 and contradicts the instruction not to edit root `.agents/` SSOT except result artifacts. Remediation:
  ```powershell
  git restore -- .agents/mcp.json .agents/mcp_config.json
  # keep only .agents/results/* QA/plan/result artifacts
  ```

## Step 6 — Alignment Review (T1-T10 / C1-C7)

| Item | Status | Evidence |
|------|--------|----------|
| T1 PowerPoint rename | PASS | `packages/pros-cli/src/mcp-powerpoint-local.ts:25-27` server name `powerpoint-local`; `pptx_*` tools preserved. |
| T2 canonical Office bins/server names | FAIL | Package bins are canonical (`package.json:9,12-14`), but runtime workflow/manifest still uses `pros-mcp-microsoft-graph`. |
| T3 Excel local core | PASS | `excel-local.ts` implements inspect/extract/read/plan/apply with workspace guard calls. |
| T4 Excel MCP server | PASS | `mcp-excel-local.ts:50-171` registers 5 tools; apply schema requires `confirmationStatus: "CONFIRMED"`. |
| T5 registry/capabilities | PASS | `integration-registry.ts:77-120` uses `powerpoint-local` and `excel-local`; Graph `excel.readRange` remains under Microsoft Graph (`integration-registry.ts:42-46`). |
| T6 MCP client config | PASS | `mcp-client-config.ts:780-803` emits `mcp-microsoft-graph`. |
| T7 CLI/help | PASS | Test output and docs show separate `integrations graph excel read-range` vs local `integrations excel ...`. |
| T8 Runtime/docs | FAIL | Runtime/projection stale findings above. |
| T9 Tests/stale guard | PARTIAL FAIL | Tests exist and pass, but stale guard misses runtime/projection. |
| T10 Verification | FAIL | Mechanical commands pass; stale scans do not. |

| Criterion | Status | Evidence |
|-----------|--------|----------|
| C1 | FAIL | Current runtime/projection still has `Office files`/`office-files` at manifest line 75. |
| C2 | FAIL | Runtime manifest/workflow/projection still use `pros-mcp-microsoft-graph`. |
| C3 | PASS | `excel-local` MCP and tools implemented; tests pass. |
| C4 | PASS with risk | Confirmation, backup, bounds and `.xlsm` denial covered by `excel-local.test.ts`; no blocking security issue found. |
| C5 | PASS | Target docs keep Graph Excel as DriveItem/OneDrive/SharePoint and local Excel separate. |
| C6 | FAIL | Runtime/Projection/Docs/Config are inconsistent. |
| C7 | PARTIAL FAIL | Test exists but does not catch stale runtime/projection references found by QA grep scans. |

## Step 7 — Safety/Security/Bug Review
- Safe writes: Excel apply is the only local Office write MCP; `mcp-excel-local.ts:148-155` requires `confirmationStatus: "CONFIRMED"`; `excel-local.ts:946-974` validates confirmation, preview ID, path match and source hash.
- Workspace Guard: Excel read/apply uses `validateWorkspacePath` at `excel-local.ts:540` and `excel-local.ts:954`; symlink escape test exists.
- Backup: `excel-local.ts:1026-1028` copies a backup before write.
- Macro deny: `excel-local.ts:960-963` denies `.xlsm` writes.
- Secret redaction: `mcp-common.ts:35-38,160-184` redacts secret-like keys and removes `approvalToken`; `mcp-servers.test.ts:87-98` covers this.
- `npm audit --audit-level=moderate`: 0 vulnerabilities.
- Open risk: Excel writer’s string-write path for workbooks without existing shared strings should be strengthened with content-type/relationship regression coverage before SHIP.

## Step 8 — Regression Review
- `npm run typecheck`: PASS.
- `npm run lint`: PASS.
- `npm test`: PASS, 24/24 files, 188 tests, 1 skipped.
- `npm run build`: PASS.
- `npm run coverage`: PASS, line coverage 69.55%.
- Targeted stale scans: FAIL as documented above.

## Quality Score Post-VERIFY
Baseline IMPL: 91.43.

| Dimension | Score | Detail |
|-----------|------:|--------|
| Correctness | 70 | Tests pass, but criteria C1/C2/C6/C7 are not satisfied by actual files/scans. |
| Security | 88 | No audit vulnerabilities; write safety controls verified; out-of-scope SSOT change risk remains. |
| Performance | 90 | No regression observed. |
| Coverage | 69.55 | Coverage output: All files line coverage 69.55%. |
| Consistency | 70 | Type/lint pass, but runtime/projection/config names inconsistent. |
| **Composite** | **77.43** | Grade B; delta **-14.00** vs 91.43. |

## Acceptance Criteria Checklist
- [x] All files in review scope inspected directly or through targeted scans.
- [x] Automated checks run: typecheck, lint, test, build, audit, coverage.
- [x] Findings include severity, file:line, evidence, and remediation.
- [x] CRITICAL/HIGH count included: CRITICAL 0 / HIGH 3.
- [x] QA artifacts written under `.agents/results/` with session ID.

## Open Risks
- Fix required before VERIFY_GATE can pass: update runtime/projection stale `pros-mcp-*` and `office-files` references, then expand stale guard coverage.
- Historical docs under `docs/plans/**` intentionally contain old names; either document allowlists or restrict automated stale scans to current user-facing/runtime surfaces.
- Worktree contains unrelated `.agents/` and `.serena/` changes; isolate or revert before SHIP to avoid shipping local agent config drift.
