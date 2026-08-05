# Task Board — Pros Global MCP Runtime

**Session**: 20260714-210942
**Plan**: `docs/plans/work/031-pros-global-mcp-runtime.md`
**Contract**: `.agents/results/api-contracts/pros-global-mcp-runtime-20260714.md`
**Ralph**: `session-ralph-20260714-210942` (C1-C5 PENDING)
**Amended**: 2026-07-14 — Serena removed from Pros-managed scope (developer-local); Office MCPs only.

## Amendment Summary

Serena remains **developer-local**; Pros MUST NOT write/read/manage a global Serena client entry. Global Pros MCP configuration continues for **Office MCPs only** (docx-local, excel-local, powerpoint-local). OpenCode uses validated `cwd: "."`; AnythingLLM Office includes rejected with `unsupported_client_capability`. Old T1 (Serena `--project` validation) and old T5 (Serena as managed include) removed. Tasks renumbered.

## Task ID Mapping

| Old | New | Note |
|-----|-----|------|
| T1 | — | REMOVED (Serena `--project` validation) |
| T2 | T1 | Workspace validation (Office MCPs only) |
| T3 | T2 | CLI contract + status codes |
| T4 | T3 | Office MCPs as managed includes |
| T5 | — | REMOVED (Serena as managed include) |
| T6 | T4 | Global SSOT + idempotent sync |
| T7 | T5 | Regression tests |
| T8 | T6 | Windows smoke tests |
| T9 | T7 | Runtime docs update |
| T10 | T8 | Migration + release checklist |
| T11 | T9 | Workflow resources sync |

## Active Tasks

| ID | Title | Agent | Prio | Status | Deps |
|----|-------|-------|------|--------|------|
| T1 | Office-MCP-Workspace validieren (OpenCode cwd:".", AnythingLLM ablehnbar) | debug | P0 | TODO | - |
| T2 | CLI-Vertrag + Statuscodes (Office-MCPs, kein Serena) | backend | P0 | TODO | T1 |
| T3 | Office-MCPs als Includes mit Workspace-Schutz | backend | P0 | TODO | T1,T2 |
| T4 | Globale SSOT + idempotente Sync (Office-MCPs) | backend | P0 | TODO | T2 |
| T5 | Regressionstests (Secrets/$PWD/cwd:"."/Idempotenz/Fehlercodes) | qa | P0 | TODO | T2,T3,T4 |
| T6 | Windows-Smoke-Tests (Office-MCPs) | qa | P1 | TODO | T1-T5 |
| T7 | Runtime-Hilfe aktualisieren (Serena developer-local) | docs | P1 | TODO | T1-T6 |
| T8 | Migration + Release-Checkliste | qa | P2 | TODO | T5,T6,T7 |
| T9 | Workflow-Ressourcen synchronisieren | docs | P1 | TODO | T1-T6 |

## Workspace Decision

- OpenCode: Office-MCP entries use `cwd: "."` (validated client-context)
- AnythingLLM: Office-MCP includes rejected with `unsupported_client_capability`
- Serena: NOT managed by Pros (developer-local only)

## Critical Path

T1 -> T2 -> T3 -> T5 -> T6 -> T7 -> T8

## Blocking Risk

REDUCED — no Serena `--project` blocker. T1 validates only Office-MCP workspace (`cwd: "."`), which is simpler.

## Ralph Criteria Mapping

- C1: T1-T4 implementieren Office-MCP-globale Verwaltung, T5 testet
- C2: T2-T3 implementieren Constraints, T5 testet Abwesenheit (Secrets/$PWD/Fallordnerpfade)
- C3: T4 implementiert Idempotenz, T5 testet Fehlercodes
- C4: T7 + T9 aktualisieren/verifizieren Runtime-Ressourcen (Serena developer-local)
- C5: Alle Tasks schliessen Tests ein

## Minimal Implementation Files

1. `packages/pros-cli/src/mcp-client-config.ts`
2. `packages/pros-cli/src/cli.ts`
3. `packages/pros-cli/src/mcp-client-config.test.ts`
4. `packages/pros-cli/src/cli.test.ts`
5. `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`
6. `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/mcp-architecture.md`
7. `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/verification.md`
8. `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/auth-and-credentials.md`
9. `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/debugging.md`
10. `runtime/pros/pros-runtime-manifest.md`
