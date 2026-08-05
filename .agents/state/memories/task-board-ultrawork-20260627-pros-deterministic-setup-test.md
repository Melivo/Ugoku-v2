# Task Board — ultrawork-20260627-pros-deterministic-setup-test

**Session**: ultrawork-20260627-pros-deterministic-setup-test
**Plan**: `.agents/results/plan-ultrawork-20260627-pros-deterministic-setup-test.json`
**Source**: `plans/pros-enduser-deterministic-setup-test-20260624`
**Status**: COMPLETED

## Board

| # | Task | Agent | Pri | Status | Deps | Checkpoint |
|---|------|-------|-----|--------|------|------------|
| 1 | Host-Inventar und Vorbedingungen erfassen | qa | P0 | DONE | - | CP-01 |
| 2 | Bestehende Pros-managed MCP-Konfiguration sichern und wipen | qa | P0 | DONE | 1 | CP-02 |
| 3 | pros CLI installieren/aktualisieren | qa | P0 | DONE | 1 | CP-03 |
| 4 | pros auth pruefen/setzen | qa | P0 | DONE | 3 | CP-04 |
| 5 | Frischen Endnutzer-Fallordner initialisieren | qa | P0 | DONE | 3,4 | CP-05 |
| 6 | Globale Tool-Skills installieren/aktualisieren | qa | P0 | DONE | 5 | CP-06 |
| 7 | HubSpot MCP-App und Credentials vorbereiten | qa | P0 | DONE | 6 | CP-07 |
| 8 | Kanonischen README-Mistral-Prompt ausfuehren | qa | P0 | DONE_WITH_DEVIATION | 5,7 | CP-08 |
| 9 | OpenCode HubSpot MCP verifizieren | qa | P0 | DONE | 8 | CP-09 |
| 10 | AnythingLLM HubSpot MCP per Agent/WebSocket verifizieren | qa | P0 | DONE | 8 | CP-10 |
| 11 | Serena isoliert ohne echte Konfig-Aenderung testen | qa | P0 | DONE | 5 | CP-11 |
| 12 | Sicherheits- und Secret-Schutzchecks | qa | P0 | DONE | 9,10,11 | CP-12 |
| 13 | README und Runtime-Doku gegen realen Ablauf pruefen | docs-qa | P1 | DONE | 12 | CP-13 |
| 14 | Abweichungen und Release-Schritte erfassen | pm-qa | P1 | DONE | 13 | CP-14 |

## User-Freigabe-Momente
- CP-02 Wipe (destruktiv)
- CP-04 Auth-Token via stdin
- CP-07 Client Secret via stdin
- CP-09 OAuth-Browser-Flow
- CP-14 Planstatus -> Completed

## Phase Mapping (Ultrawork)
- IMPL (Step 5): Tasks 1-8 (Setup durch Mistral-Prompt)
- VERIFY (Steps 6-8): Tasks 9-12 (Verifikation + Secret-Sweep)
- REFINE (Steps 9-13): Bedingter Skip (Test-Workflow; Korrektur nur bei Abweichungen)
- SHIP (Steps 14-17): Tasks 13-14 (Doku-Sync + Closure)

## Reviews
- Step 2 Completeness: PASS
- Step 3 Meta: PASS
- Step 4 Over-Engineering: PASS
