# PM-Ergebnis: Pros MCP Setup Repair (Work-Workflow Step 2)

> Session: `pros-mcp-setup-repair-20260707` | Datum: 2026-07-07 | Sprache: Deutsch | Runtime-Vendor: OpenCode

## Status

**SUFFICIENT — bestaetigt ohne Plan-Aenderung.** Step 3 (Review mit Nutzer) ist freigegeben, sobald der Nutzer den Plan abnimmt.

## Zusammenfassung

Der bestehende Plan `.agents/results/plan-pros-mcp-setup-repair-20260707.json` wurde gegen die Requirements, den Boundary Contract und die tatsaechliche Codebasis validiert. Die beteiligten Domains, die CLI/MCP/Credential-Grenzen, die Task-Priorisierung, Abhaengigkeiten, Agent-Zuordnungen und Akzeptanzkriterien sind stichhaltig und mit den referenzierten Code-Symbolen (`zip.extract`, `buildMicrosoftAuthorizationUrl`, `mcp-client-config.ts`-Funktionen, `QNAP_MCP_ASSISTANT_CREDENTIAL_TARGET`) sowie den Vorplan-Artefakten (019, 020, design 005) konsistent. Es sind keine Luecken festgestellt worden, die eine Aenderung erzwingen. Der Plan wurde daher **nicht geaendert**.

## Beteiligte Domains

- **backend** — CLI-Fix `pros init`-Extraktion, Microsoft Graph Setup-Konfiguration, QNAP Token-stdin/Credential-Target, MCP-Konfigstatus.
- **qa** — Init-/Zip-Regressionstests, QNAP Credential-/MCP-Tests, End-to-end Smoke-Run, Release-/Rollback-Check.
- **docs** — Microsoft Graph Setup-Doku-Sync, HubSpot-Nacharbeiten/Doku-Drift.
- *Nicht beteiligt:* frontend, mobile, database (kein UI-/App-/Schema-Change im Scope).

## Contract-Bewertung

Der Contract (`.agents/results/api-contracts/pros-mcp-setup-repair.md`) ist ein **CLI/MCP/Setup-Boundary-Contract**, kein REST-API-Contract. Das ist korrekt gewaehlt, weil der Scope keine neue oeffentliche REST API enthaelt (explizit out-of-scope) und die Arbeit CLI-Kommandos, MCP-Client-Konfiguration, OS Credential Store und externe OAuth/QNAP-Grenzen kreuzt.

Bewertung je Dimension:

| Dimension | Bewertung | Hinweis |
|-----------|-----------|---------|
| CLI-Kommando-Grenzen | Ausreichend | `pros init`, `graph start/status`, `qnap token set/status`, `mcp configure` mit Description/Auth/Input/Required-behavior/Success/Error |
| Auth & Secret Handling | Ausreichend | Delegated OAuth, Credential-Store-Targets, explizites Secret-Verbot fuer Client-Config/Repo/Logs |
| MCP-Runtime-Grenzen | Ausreichend | microsoft-graph, qnap-mcp-assistant, hubspot mit Local-Command, Remote-Target, Secret-Freiheit |
| Acceptance Gates | Ausreichend | 6 Gates decken alle Must-Haves + Sicherheitsreview |
| Redirect-URI-Default | Konsistent | Contract/Code: `http://localhost:53682/oauth/microsoft/callback` (Bericht nannte abweichend `:19876` — Task 4 korrigiert die Doku) |
| Credential-Target | Konsistent | `pros:qnap:mcp-assistant` in Contract, Code und Task 5/6 |

Kontrakte sind ausreichend definiert fuer Step 4 (Agent-Spawning).

## Task-Priorisierung

### P0 — Kritisch (Blocker fuer Setup-Nutzung)

| # | Task | Agent | Deps |
|---|------|-------|------|
| 1 | Windows-`pros init`-Extraktion reparieren (PowerShell `Expand-Archive`-Argumentbindung bei Leerzeichen) | backend | — |
| 2 | Init-/Zip-Regressionstests erweitern (Leerzeichen-Pfad, unsichere Archive, laute Extraktionsfehler) | qa | 1 |
| 3 | Microsoft-Graph Setup-Konfiguration konsolidieren (Client-ID-Quelle, Redirect-Default, AADSTS700016 als App/Tenant-Problem) | backend | — |
| 4 | Microsoft-Graph Setup-Dokumentation synchronisieren (eindeutige Redirect-URI/Client-ID, AADSTS-Troubleshooting) | docs | 3 |
| 5 | QNAP Token-stdin UX und Credential-Target klaeren (`--stdin`-Bedienung, dokumentiertes Target) | backend | — |
| 6 | QNAP Credential-/MCP-Tests erweitern (stdin Erfolg/leer, Credential-Target-Status, secret-free Config) | qa | 5 |

### P1 — Wichtig (Stabilitaet/Doku)

| # | Task | Agent | Deps |
|---|------|-------|------|
| 7 | MCP-Konfigurationsstatus fuer OpenCode/AnythingLLM validieren (idempotent, fremde Eintraege bewahrt, klare Credential-Fehler) | backend | 3, 5 |
| 8 | HubSpot-Nacharbeiten und Doku-Drift bereinigen (SecureString-Umwege, Neustart/OAuth-Abschluss, keine Secrets im Flow) | docs | 7 |
| 9 | End-to-end Smoke-Run definieren und ausfuehren (init, Graph-Status, QNAP-Tokenstatus, HubSpot-Status, MCP-Dry-Runs) | qa | 1-8 |

### P2 — Nice-to-have (Release-Reife)

| # | Task | Agent | Deps |
|---|------|-------|------|
| 10 | Release-/Rollback-Check vorbereiten (CLI-Version, Release-Notizen, manuelle Verifikation, Rollback-Hinweise) | qa | 9 |

## Dependencies & Parallelitaet (fuer Step 4)

- **P0 Welle A (parallel):** Tasks 1, 3, 5 — keine Abhaengigkeiten untereinander, getrennte Dateien (`zip.ts`, `microsoft-oauth.ts`, `mcp-client-config.ts`/`cli.ts`-stdin).
- **P0 Welle B (parallel nach Welle A):** Tasks 2, 4, 6 — jeweils abhaengig von ihrem Fix-Task.
- **P1:** Task 7 nach 3+5; Task 8 nach 7; Task 9 nach allen 1-8.
- **P2:** Task 10 nach 9.

Abhaengigkeiten sind korrekt und minimal; maximale Parallelitaet wird gewahrt. Keine zirkulaeren Abhaengigkeiten.

## Akzeptanzkriterien-Checkliste (Plan-Ebene)

- [x] Jeder Task hat testbare Akzeptanzkriterien.
- [x] Priorisierung P0/P1/P2 verhaeltnismaessig (Root-Cause-Fixes = P0; Doku/Validierung = P1; Release = P2).
- [x] Agent-Zuordnung: backend/qa/docs; jeder Task von einem Agent abschliessbar.
- [x] Sicherheits-Aspekte in Tasks verankert (secret-free Config in 6/7/9; Contract-Gate fuer Security-Review) — dedizierter Security-Task nicht noetig, da Work-Workflow Step 6 QA-Security-Review durchfuehrt.
- [x] Testing in Tasks verankert (2, 6 Regression; 9 Smoke).
- [x] Dokumentation in Tasks verankert (4, 8).
- [x] Root Causes werden vor Symptomen adressiert (Manifest-Fehler, AADSTS, needs_credential als Folge eingestuft).
- [x] Scope/Out-of-Scope klar (kein Azure-Admin, kein QNAP-Rotation, kein HubSpot-Reimpl, keine neue REST API).
- [x] Secrets werden in keinem Artefakt/Log/Config erwartet (Constraint + Contract-Gate).
- [x] Vorplan-Entscheidungen (019/020/design 005) bleiben gueltig.

## Offene Risiken & Empfehlungen

1. **`readTokenFromStdin` ist Shared Helper** (Gitea token, HubSpot secret, QNAP token). Task 5 fokussiert QNAP-UX; eine UX-Verbesserung am Helper kommt allen drei zugute. Keine Plan-Aenderung noetig, aber Task 5 sollte die geteilte Natur beachten, um keine Regressionen bei Gitea/HubSpot einzufuehren.
2. **AADSTS700016 ist extern** (Azure AD App/Tenant), nicht durch Code loesbar. Task 3 kann nur Status/Message-Klassifizierung verbessern (`classifyTokenError`), nicht den externen Zustand beheben. Akzeptanzkriterium spiegelt das korrekt wider. Risiko: Endnutzer muss dennoch die Azure-App korrigieren.
3. **Windows PowerShell-Testbarkeit**: Task 2 muss Leerzeichen-Pfade plattformabhaengig testen; nicht-Windows-Runner koennen das Verhalten nicht voll reproduzieren. Smoke (Task 9) muss auf Windows laufen.
4. Keine Blocker fuer Step 3.

## Empfehlung fuer Step 3

**Step 3 ist Nutzerfreigabe-ready.** Der Plan ist vollstaendig, priorisiert, konsistent mit Code und Contract und bedarf keines separaten Security-/Frontend-/Mobile-Tasks. Nach Bestaetigung kann Step 4 die P0-Welle A (Tasks 1, 3, 5 parallel) spawnen.

## Geaenderte Dateien

- **Plan:** nicht geaendert (`.agents/results/plan-pros-mcp-setup-repair-20260707.json` bestaetigt wie ist).
- **PM-Ergebnis (neu):** `.agents/results/result-pm-pros-mcp-setup-repair-20260707.md` (diese Datei).
- Keine Code- oder `.agents/`-SSOT-Aenderungen.
