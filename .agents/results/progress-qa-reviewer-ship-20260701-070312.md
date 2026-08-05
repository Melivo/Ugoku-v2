# QA Ship Progress — 20260701-070312

Status: completed

## Step 14 — Quality Review
- `npm run typecheck`: PASS (`tsc -b --pretty false`).
- `npm run lint`: PASS (Biome checked 65 files, no fixes applied).
- `npm test`: PASS (24 test files, 188 tests passed, 1 skipped).
- `npm run build`: PASS (`tsc -b`).
- `npm run coverage`: PASS (24 test files, 188 passed, 1 skipped; all-files line coverage 69.55%).
- `npm audit --audit-level=moderate`: PASS (0 vulnerabilities).

## Step 15 — UX / CLI Flow Verification
- PASS. `node packages/pros-cli/dist/cli.js --help` trennt Graph-Cloud-Excel (`integrations graph excel read-range <driveItemId> ...`) klar von lokalem Excel (`integrations excel inspect|extract|read-range <path> ...`).
- PASS. PowerPoint (`integrations pptx inspect|extract`) und DOCX (`integrations docx inspect|extract`) sind in der Hilfe entdeckbar.
- PASS. `integrations preflight` bestaetigt MCP-Setup als validierte Runtime-Manifest-Pfade; Package-Bin-Check bestaetigt vorhandene Dist-Ziele fuer `mcp-microsoft-graph`, `mcp-docx-local`, `mcp-powerpoint-local`, `mcp-excel-local` sowie die weiterhin `pros-mcp-*` QNAP/HubSpot-Bins.

## Step 16 — Related Issues / Cascade Impact Review
- PASS. Targeted stale scans fuer `runtime/pros` und `build/runtime-projection` fanden keine retired Office-MCP-Namen.
- PASS. Source-Import-Scan fand nur den absichtlichen Guard-Treffer in `stale-name-guard.test.ts`, keine aktiven Legacy-Imports auf `office-files`/`mcp-office-files`.
- FAIL/WARNING. Projection-Metadaten sind nicht vollstaendig versionssynchron: Package und Lockfile stehen auf `0.5.25`, die checked-in Runtime-Projection-Metadaten noch auf `0.5.24`.

## Step 17 — Deployment Readiness
- PASS. High-confidence Secret-Scan auf Source/Runtime/Docs/Projection fand keine echten Geheimnisse; Treffer in Tests sind Dummy-Token-Fixtures.
- PASS. Root `.agents/` SSOT wurde nicht bearbeitet; bestehende `.agents/mcp*.json` Drift bleibt der bereits bekannte, nicht Plan-21-blockierende Hinweis.
- FAIL/WARNING. Deployment-Metadaten der Runtime-Projection muessen vor Ship auf `0.5.25` regeneriert/synchronisiert werden.
- LOW note. `npm run release:dry-run` hat durch `cleanup()` den lokalen `build/`-Ordner entfernt; QA hat den Zustand danach wiederhergestellt. Das ist als separates Release-Script-Hygiene-Thema dokumentiert.

## Step 17.1 — Final Score
- Final score: 89/100.
- SHIP_GATE: FAIL aus QA-Sicht bis die Projection-Versionen synchron sind.
- CRITICAL/HIGH: 0/0.
- User final approval pending: ja.
