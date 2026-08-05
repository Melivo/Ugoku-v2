# PLAN-Phase Ergebnis — Plan 032: MCP-Workflow deterministisch verbessern

> Ultrawork PLAN (Steps 1–4). Keine Codeänderungen. Basiert auf Serena-/Grep-Symbolanalyse des `@pro-select/pros-cli` TypeScript-Pakets und der Runtime unter `runtime/pros/.agents/`.

```
CHARTER_CHECK:
- Clarification level: LOW
- Task domain: planning
- Must NOT do: (1) Code implementieren, (2) .agents/ SSOT ändern, (3) Live-Provider ohne Zustimmung prüfen
- Success criteria: 12 Tasks mit Dateien/Symbolen/Tests/Reihenfolge mechanisch zugeordnet; Abhängigkeitssichere Wellen; Testbefehle ausführbar
- Assumptions: Serena-MCP (getimed out) → Grep/Glob/Read als Fallback genutzt; Befunde symbolgenau verifiziert
```

**Status**: PLAN_GATE-vorbereitet (wartet auf User-Confirm)
**Quelle**: `docs/plans/work/032-mcp-workflow-deterministisch-verbessern.md`
**Maschinen-Plan**: `.agents/results/plan-032.json`

---

## 1. Codebasis-Befund (Serena/Grep-Analyse)

**Paket**: `packages/pros-cli/src/` (ESM TypeScript, Vitest, Biome). Befehls-Parsing + I/O in `cli.ts`.

### Wiederverwendbare Bausteine (bestätigt vorhanden)

| Symbol | Datei:Zeile | Relevanz |
|---|---|---|
| `McpStatusCode` | `mcp-client-config.ts:26` | Status-Vokabular (ready/configured/unchanged/needs_credential/unsupported_client_capability/invalid_workspace_mode/workspace_unavailable/warning/failed) |
| `McpCommandResult` | `mcp-client-config.ts:43` | Bestehendes Result-Shape — **FEHLT** schemaVersion/command/target/nextAction/evidence |
| `McpCheck` | `mcp-client-config.ts:37` | name/passed/message — wiederverwendbar für `checks[]` |
| `getMcpStatus` | `mcp-client-config.ts:110` | Statischer Status inkl. `probe`-Stummel |
| `configureMcpClient` | `mcp-client-config.ts:184` | Idempotente Client-Konfiguration |
| `getManagedClientDoctorChecks` | `mcp-client-config.ts:633` | Config-/Credential-Evidenz pro Client |
| `getMcpDoctorChecks` | `mcp-client-config.ts` (von `doctor.ts:5` importiert) | Doctor-Checks |
| `HubSpotCredentialOptions` / `getHubSpotMcpCredentialTarget` | `mcp-client-config.ts:66` / `:102` | HubSpot-Credential-Grenze |
| `SECRET_VALUE_PATTERN` / `hasSecretLikeValue` | `mcp-client-config.ts:99` | Bestehende Redaction — für `evidence` nutzen |
| `runQnapMcpAssistantBridge` | `mcp-qnap-assistant.ts:62` | Secret-freier QNAP-Wrapper |
| `checkQnapMcpAssistantReadiness` | `mcp-qnap-assistant.ts:45` | **Nur** ready/needs_credential/failed — MUSS erweitert werden |
| `QnapStatusCode` | `qnap-files.ts:13` | File-Station-Status (nicht MCP-Assistant-Diagnose) |
| `resolveMicrosoftRedirectUri` / `createMicrosoftOAuthStart` | `microsoft-oauth.ts:265` / `~312` | Liest `PROS_MICROSOFT_CLIENT_ID`/`_TENANT_ID` aus ENV — **MUSS** persistente App-Config bekommen |
| `writeMcpResult` | `cli.ts:1487` | Gibt aktuell **Menschen-lesbaren Text** aus — kein JSON-Pfad |
| `parseArgs` | `cli.ts:258` | **KEIN** `--json`-Flag vorhanden |

### Bestätigte Lücken (Neuimplementierungen)

- **Kein** `--json`-Flag, keine versionierte JSON-Ausgabe (`writeMcpResult` = Klartext mit Titelzeile).
- **Keine** Befehle `integrations graph app discover`, `integrations graph app configure`, `mcp qnap diagnose` (Grep über `cli.ts` = 0 Treffer).
- **Keine** Strings `nextAction`, `evidence`, `client_restart_required`, `needs_selection`, `blocked_precondition` in `cli.ts`.
- **Keine** `scripts/verify-opencode-mcps.ps1` (repo `scripts/` enthält nur `.js/.py/.sh/.css`).
- Graph-App-Discovery läuft heute über Azure-CLI-Text + ENV-Variablen; keine persistente, prozessunabhängige Pros-App-Konfiguration.
- QNAP-Diagnose kennt heute nur ready/needs_credential/failed; keine Trennung von token_missing/network_unreachable/tls_untrusted/credential_rejected/endpoint_error.

### Bestehende Tests (Vitest `test()`, NICHT `it()`)

| Datei | describe | Abdeckung für Plan |
|---|---|---|
| `mcp-client-config.test.ts:57` | `mcp-client-config` | ~30 Tests: configureMcpClient-Idempotenz, Redaction, Client-Verhalten, getMcpStatus |
| `mcp-qnap-assistant.test.ts:22` | `mcp-qnap-assistant` | runQnapMcpAssistantBridge, Readiness |
| `mcp-hubspot-remote.test.ts:20` | `mcp-hubspot-remote` | HubSpot-Remote-Bridge |
| `cli.test.ts:154` | `runCli` | CLI-Dispatch: help, `integrations status` (607), `mcp status` (630), `mcp qnap token status` (814), `integrations qnap status` (1109), OAuth-Callback (937+) |
| `microsoft-oauth.test.ts` | — | DEFAULT_REDIRECT_URI, redirectUri-Validierung |
| `integrations.test.ts:89` | `integrations` | Profil-Logik |

---

## 2. Mechanisch prüfbare Taskliste

Legende: ✎ ändern · ＋ neu · ★ primär · bestehende Tests in Klammern.

### Task 1 — Session-Fixtures + Statusvertrag (debug · P0 · deps: — · Welle 0)
- **Ziel**: Kanonisches Status-Vokabular + reproduzierbare Fixtures pro bestätigtem Sessionfehler (erwarteter Status/Exit-Code/Folgeaktion).
- **Dateien**: ＋ `packages/pros-cli/src/mcp-status-contract.ts` (Status-Union + Exit-Code-Map) · ＋ `tests/fixtures/mcp-session/*.json` · ＋ `docs/plans/work/_fixtures/032-readme.md`
- **Symbole referenzieren**: `McpStatusCode` (mcp-client-config.ts:26), `QnapMcpAssistantStartResult.status` (mcp-qnap-assistant.ts:41), `IntegrationStatusCode` (integration-config.ts:17)
- **Neue Statuswerte (Vertrag)**: `ready`, `needs_selection`, `blocked_precondition`, `needs_credential`, `client_restart_required`, `network_unreachable`, `tls_untrusted`, `credential_rejected`, `endpoint_error`, `token_missing`, `connected`, `function_verified`, `not_run`, `aborted`
- **Tests**: (keine — Setup) — Acceptance: jeder Sessionfehler als Fixture mit {Eingabe → Status, Exit-Code, Folgeaktion}
- **Mechanische Prüfung**: Fixtures laden → Status/Exit-Erwartung pro Fixture vorhanden

### Task 2 — Versioniertes JSON- + Exit-Code-Schema (backend · P0 · deps: 1 · Welle 1) ★ LINCHPIN
- **Ziel**: `--json`-Pfad mit `schemaVersion`/`command`/`status`/`client`/`target`/`changed`/`checks`/`nextAction`/`evidence(redacted)` + stabile Exit-Codes.
- **Dateien**: ✎ `mcp-client-config.ts` (erweitere `McpCommandResult:43`; Serializer; Exit-Code-Funktion) · ✎ `cli.ts` (`parseArgs:258` `--json`-Flag; `writeMcpResult:1487` JSON-Zweig; Exit-Code-Mapping in `runCommand`)
- **Symbole**: `McpCommandResult`, `writeMcpResult`, `parseArgs`
- **Redaction**: `SECRET_VALUE_PATTERN:99` / `hasSecretLikeValue` auf `evidence` anwenden
- **Tests**: ✎ `mcp-client-config.test.ts:57` (Schema-Stabilität, Wiederholung = identisch, Redaction) · ✎ `cli.test.ts:154` (`--json`-Ausgabe + Exit-Code)
- **Mechanische Prüfung**: `npx vitest run packages/pros-cli/src/mcp-client-config.test.ts -t "json"`

### Task 3 — Graph-App-Discovery + persistente App-Konfiguration (backend · P0 · deps: 1,2 · Welle 2)
- **Ziel**: `integrations graph app discover --redirect-uri ... --json` (redirect-first, `needs_selection` bei Mehrdeutigkeit) + `graph app configure --client-id --tenant-id --json` (persistent, kein `$env:`-Erbe).
- **Dateien**: ＋ `microsoft-app-config.ts` (persistente nicht-geheime App-Konfiguration) · ✎ `microsoft-oauth.ts` (`resolveMicrosoftRedirectUri:265`, `createMicrosoftOAuthStart:~312` lesen aus persistenter Config statt nur ENV) · ✎ `cli.ts` (2 neue Befehlszweige + Help-Text:179/202/1230)
- **Symbole**: `resolveMicrosoftRedirectUri`, `createMicrosoftOAuthStart`, `MicrosoftOAuthStartResult`
- **Tests**: ✎ `microsoft-oauth.test.ts` (redirect-first, persistente Config ohne ENV-Erbe, `needs_selection`) · ✎ `cli.test.ts:154` (Help enthält `graph app discover/configure`)
- **Mechanische Prüfung**: `npx vitest run packages/pros-cli/src/microsoft-oauth.test.ts`
- **DON'T**: kein geratener Display Name; keine Abhängigkeit von geerbten `$env:`-Werten

### Task 4 — QNAP-Diagnose mit Fehlerklassifikation (backend · P0 · deps: 1,2 · Welle 2)
- **Ziel**: `mcp qnap diagnose --json` liefert getrennt `token_missing|network_unreachable|tls_untrusted|credential_rejected|endpoint_error|ready`, secret-frei.
- **Dateien**: ✎ `mcp-qnap-assistant.ts` (erweitere `checkQnapMcpAssistantReadiness:45` ODER ＋ `diagnoseQnapMcpAssistant`; erweitere `QnapMcpAssistantStartResult:41`) · ✎ `cli.ts` (neuer Zweig `mcp qnap diagnose`)
- **Symbole**: `checkQnapMcpAssistantReadiness`, `runQnapMcpAssistantBridge:62`, `QNAP_MCP_ASSISTANT_REMOTE_URL`
- **Tests**: ✎ `mcp-qnap-assistant.test.ts:22` (jede Fehlerklasse, secret-frei)
- **Mechanische Prüfung**: `npx vitest run packages/pros-cli/src/mcp-qnap-assistant.test.ts`
- **DON'T**: leeres `Certificate` ≠ TLS-Fehler; Server-Zertifikat niemals als Root-CA importieren; kein `NODE_TLS_REJECT_UNAUTHORIZED=0`

### Task 5 — HubSpot-Credential/Configure deterministisch (backend · P0 · deps: 1,2 · Welle 2)
- **Ziel**: Genau ein maskierter stdin-Pfad, kein zweiter Prompt, idempotente Statuswerte.
- **Dateien**: ✎ `cli.ts` (`mcp hubspot credentials set`-Zweig ~1302–1315; sicherstellen genau eine stdin-Lesung via `clientSecretFromStdin`/`--client-secret-stdin`) · ✎ `mcp-client-config.ts` (deterministische Result-Shape für set/status/clear/configure)
- **Symbole**: `HubSpotCredentialOptions:66`, `getHubSpotMcpCredentialTarget:102`, `HUBSPOT_CREDENTIAL_TARGET:85`
- **Tests**: ✎ `mcp-client-config.test.ts:57` (Idempotenz set, kein 2. Prompt, Status stabil) · ✎ `cli.test.ts:154` · ✎ `mcp-hubspot-remote.test.ts:20`
- **Mechanische Prüfung**: `npx vitest run packages/pros-cli/src/mcp-hubspot-remote.test.ts`

### Task 6 — Workflow als Router + Zustandsmaschine (backend · P0 · deps: 1 · Welle 1)
- **Ziel**: Hauptdatei nur Routing/Gates; Detailwissen einmalig in flachen Ressourcen; credential-freie Ziele zuerst.
- **Dateien**: ✎ `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md` (264-Zeilen-Prozedur → kurzer Router + Phasen/Gates) · ＋ `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/execution-protocol.md` (Zustandsmaschine, unabhängige Zielverarbeitung)
- **Bestehende Ressourcen bleiben**: `verification.md`, `mcp-architecture.md`, `debugging.md`, `auth-and-credentials.md`
- **Konsistenz prüfen**: `runtime/pros/.agents/skills/werkzeuge-mcp-einrichtung/SKILL.md` (Doppelung auflösen)
- **Tests**: (keine — Text) — Acceptance: Hauptdatei = nur Router+Gates; kein Detail-Duplikat
- **Mechanische Prüfung**: manuelle Review-Checkliste (Hauptdatei-Länge ↓, Resource-Einmaligkeit)

### Task 7 — Ressourcen: Verhalten/Fehler/Edge-Cases (backend · P0 · deps: 3,4,5,6 · Welle 3)
- **Ziel**: DO/DON'T/WHEN X THEN Y, High-Risk-Blacklist, sofortiger STOP, unabhängige Zielverarbeitung explizit.
- **Dateien**: ＋ `resources/agent-behavior.md` · ＋ `resources/terminal-contract.md` (Befehle, JSON-Schema, Exit-Codes, erwartete Ausgaben aus Plan-Tabelle) · ＋ `resources/error-playbook.md` (Symptom → Fehlerklasse → genau eine Folgeaktion) · ✎ `verification.md`/`debugging.md` (Verweis auf neue Befehle)
- **Quelle**: Plan-Abschnitte "CLI And Terminal Contract" + "Required Agent Behavior"
- **Tests**: (keine — Text)
- **Mechanische Prüfung**: Checkliste pro "Required Agent Behavior"-Zeile = 1 kodierter Eintrag

### Task 8 — OpenCode-CLI-Verifikation + Parser-Skript (backend · P0 · deps: 2,6,7 · Welle 4)
- **Ziel**: `scripts/verify-opencode-mcps.ps1` wertet `opencode mcp list` + `opencode run --format json` aus (Servername, Toolaufruf, Resultat, Mutationsfreiheit).
- **Dateien**: ＋ `scripts/verify-opencode-mcps.ps1` (Repo-Root `scripts/`, neu) · ＋ `resources/opencode-verification.md`
- **Befehle**: `opencode mcp list` (statisch) + `opencode run --format json --dir "<fallordner>" --title "pros-mcp-verify-<target>" --agent build "<read-only-Auftrag>"`
- **DON'T**: kein `opencode debug config` (gibt Secrets aus); `failed` in `mcp list` → keinen Funktionstest starten
- **Tests**: (Skript-Smoke, wenn möglich Pester/PowerShell) — Acceptance: Parser validiert Servername/Toolaufruf/Resultat/Mutationsfreiheit; kein Contract-Drift durch Raten
- **Mechanische Prüfung**: `pwsh scripts/verify-opencode-mcps.ps1 -DryRun` (sofern implementiert)

### Task 9 — CLI-Unit-/Integrations-/Sicherheitsregressionstests (qa · P0 · deps: 2,3,4,5 · Welle 4)
- **Dateien**: ✎ `mcp-client-config.test.ts:57` · ✎ `microsoft-oauth.test.ts` · ✎ `mcp-qnap-assistant.test.ts:22` · ✎ `mcp-hubspot-remote.test.ts:20` · ✎ `cli.test.ts:154` · ＋ Test für `microsoft-app-config.ts`
- **Abdeckung**: JSON-Schema-Stabilität, Exit-Codes, Idempotenz, Redaction, Fehlerklassen — alle ohne echte Secrets
- **Mechanische Prüfung**: `npm test` (root) — Coverage-Gate via `npm run coverage`

### Task 10 — Vorwärts-Test mit schwachen Modellen (qa · P1 · deps: 6,7,8 · Welle 5)
- **Input**: Held-out Fixtures aus Task 1 (von Trainingsfixtures getrennt).
- **Ziel**: Schwache Modelle erfinden keine Befehle/Erfolge/Zertifikatsursachen.
- **Tests**: (eval/manuell) — Acceptance: Held-out-Fixtures bestanden
- **Risiko**: benötigt tatsächliche schwache Modellläufe; nicht vollautomatisierbar

### Task 11 — Frischer Windows-E2E-Lauf (qa · P1 · deps: 8,9,10 · Welle 6)
- **Ziel**: Frischer Fallordner belegt OpenCode-Neustart, Verbindung + nicht-mutierenden Tooltest pro angefordertem Ziel.
- **DON'T**: HubSpot/QNAP-Live nur nach Zustimmung; kein `skipped-by-user` für nicht ausgeführte Ziele (sonst `not_run`/`blocked_precondition`/`aborted`)
- **Tests**: (E2E, manuell) — Acceptance: pro Ziel Evidenz oder Blocker dokumentiert
- **Mechanische Prüfung**: `pwsh scripts/verify-opencode-mcps.ps1` im frischen Fallordner

### Task 12 — Runtime-Projektion/Ressourcen/Altplaene synchronisieren (qa · P1 · deps: 3–11 · Welle 7)
- **Dateien**: ✎ `runtime/pros/pros-runtime-manifest.md` · ✎ Altpläne `026-pros-mcp-setup-repair.md`, `028-microsoft-graph-oauth-qnap-readiness.md`, `015-mcp-enduser-test.md` (abschließen/ersetzen) · ✎ ggf. `runtime/pros/.agents/skills/.../SKILL.md`
- **Acceptance**: keine widersprüchlichen Befehle; Build/Tests/Typecheck/Lint/Release-Dry-Run grün
- **Mechanische Prüfung**: `npm run build; npm run typecheck; npm run lint; npm test; npm run release:dry-run; npm run bom:check`

---

## 3. Minimale sichere Umsetzungsreihenfolge (Wellen, parallelisierbar)

```
Welle 0:  Task 1                                     (Fixtur/Vertrag — keine Code-Abhängigkeit)
Welle 1:  Task 2  ←─┐                                (Schema = Linchpin)
          Task 6  ←─┘ deps nur 1                     (Workflow-Text, parallel zu 2)
Welle 2:  Task 3 ┐
          Task 4 ├─ alle deps 1,2 (parallel)         (CLI-Erweiterungen auf neuem Schema)
          Task 5 ┘
Welle 3:  Task 7        deps 3,4,5,6                 (Ressourcen kodieren neue Befehle)
Welle 4:  Task 8        deps 2,6,7                   (Verifikationsskript)
          Task 9        deps 2,3,4,5  (parallel)     (Tests)
Welle 5:  Task 10       deps 6,7,8                   (schwache Modelle)
Welle 6:  Task 11       deps 8,9,10                  (E2E Windows)
Welle 7:  Task 12       deps 3–11                    (Synchronisation/Release)
```

**Kritischer Pfad**: 1 → 2 → (3|4|5) → 7 → 8 → 11 → 12.
**Frühester Parallelismus**: Task 6 läuft ab Welle 1 neben Task 2 (nur Text, berührt keine CLI-Symbole).

---

## 4. Testbefehle (mechanisch ausführbar)

```powershell
# Repository-Root
npm run build            # tsc -b
npm run typecheck        # tsc -b --pretty false
npm run lint             # biome check
npm test                 # vitest run (alle)
npm run coverage         # vitest run --coverage
npm run release:dry-run  # Release-Dry-Run
npm run bom:check        # BOM/Encoding

# Paket-lokal (packages/pros-cli)
npm test
npm run typecheck
npm run lint

# Einzelne Suites (schnelle Feedback-Schleife)
npx vitest run packages/pros-cli/src/mcp-client-config.test.ts
npx vitest run packages/pros-cli/src/mcp-qnap-assistant.test.ts
npx vitest run packages/pros-cli/src/microsoft-oauth.test.ts
npx vitest run packages/pros-cli/src/mcp-hubspot-remote.test.ts
npx vitest run packages/pros-cli/src/cli.test.ts

# Verifikationsskript (nach Task 8)
pwsh scripts/verify-opencode-mcps.ps1
```

---

## 5. Risiken & Preconditions

| # | Risiko / Precondition | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| R1 | `writeMcpResult` ist reiner Text; JSON-Pfad ist Breaking-Change-resistent zu halten | Task 2 bricht bestehende Konsumenten | Default = Text; JSON nur bei `--json`; bestehende `cli.test.ts`-Erwartungen prüfen |
| R2 | Graph-OAuth liest heute aus `$env:`; neue persistente Config darf ENV-Pfad nicht stilllegen | Task 3 bricht `microsoft-oauth.test.ts` | ENV als Fallback erhalten; persistente Config hat Vorrang; beide Pfade testen |
| R3 | `checkQnapMcpAssistantReadiness` hat nur 3 Status; Erweiterung berührt `runQnapMcpAssistantBridge` | Task 4 Nebenwirkung auf laufenden Bridge | Neue `diagnose*`-Funktion; Readiness-Signatur stabil halten |
| R4 | Schwache-Modell-/E2E-Tests (10/11) brauchen echte LLM- u. Windows-Umgebung + Zustimmung | Nicht in CI automatisierbar | Als manuelle Gate-Checks; Held-out Fixtures fixieren |
| R5 | HubSpot/QNAP-Livepruefungen nur nach Zustimmung (Plan-Constraint) | Task 11 blockiert ohne Freigabe | `blocked_precondition` dokumentieren; nicht simulieren |
| R6 | Runtime-Workflow (`runtime/pros/.agents/`) vs. Skill-Variante (`skills/werkzeuge-mcp-einrichtung/SKILL.md`) können driften | Task 6/12 Doppelung | Task 12 konsolidiert; genau eine Wahrheit pro Detail |
| R7 | Root `.agents/` ist Agent-SSOT — darf nicht für Endnutzer-Runtime umgebaut werden | Task 6/7/8/12 berühren nur `runtime/pros/.agents/` + repo `scripts/` | Nicht in Root `.agents/skills|workflows` schreiben |
| R8 | Kein API-Vertrag nötig (Decision Log); CLI/JSON-Vertrag ist die Grenze | Falscher Scope | Task 2 definiert den verbindlichen CLI/JSON-Vertrag |
| P1 | Serena-MCP timed out → Grep/Glob/Read genutzt; Symbolbefunde per Zeilennummer verifiziert | — | Bei IMPL erneut `find_symbol` pro Symbol bestätigen |

---

## 6. PLAN-Reviews (Ultrawork Steps 2–4)

### Step 2 — Completeness Review
- [x] Alle 12 Planaufgaben auf konkrete Dateien + Symbole + bestehende Tests abgebildet.
- [x] Bestätigte Lücken (fehlende Befehle/Flags/Skript) als Neuimplementierungen markiert.
- [x] CLI/JSON-Vertrag als Substitut für (nicht geforderten) API-Vertrag definiert.
- [x] Dependency-Graph in parallelfähige Wellen überführt; kritischer Pfad benannt.
- [x] Testbefehle pro Suite + Root-Gates gelistet.

### Step 3 — Meta Review (Selbstverifikation der Review)
- [x] Befunde sind symbol-/zeilengenau (nicht geraten): `McpCommandResult:43`, `writeMcpResult:1487`, `parseArgs:258`, `checkQnapMcpAssistantReadiness:45` etc.
- [x] Keine Aufgabe doppelt zugewiesen; jede von einem einzelnen Agenten abschließbar.
- [x] Abhängigkeiten schlüssig: Task 2 blockiert 3/4/5/9; Task 7 braucht fertige Befehle (3/4/5).
- [x] Hinweis auf ENV-Fallback (R2) verhindert stillen Bruch bestehender OAuth-Tests.

### Step 4 — Over-Engineering Review (Simplicity/MVP)
- [x] Keine neue Netzwerk-API (Plan-Decision übernommen).
- [x] Kein separater Secret-Scan-Dienst — bestehende `SECRET_VALUE_PATTERN`/`hasSecretLikeValue` wiederverwendet.
- [x] `QnapStatusCode` (File Station) NICHT für MCP-Assistant-Diagnose zweckentfremdet; stattdessen gezielte Erweiterung.
- [x] Verifikationsskript nutzt vorhandene OpenCode-CLI statt Sidecar-API/debug-config.
- [x] Workflow-Router statt Monolith; progressive Offenlegung hält Token-Budget niedrig.

---

## 7. PLAN_GATE-Checkliste

- [x] Plan dokumentiert (diese Datei + `plan-032.json`)
- [x] Annahmen gelistet (Assumptions + Risiken)
- [x] Alternativen berücksichtigt (ENV-Fallback, Diagnose-vs-Readiness-Erweiterung)
- [x] Over-Engineering-Review durchgeführt
- [ ] **User-Confirm ausstehend** ← PLAN-Phase endet hier; keine IMPL ohne Freigabe

**Nächste Aktion**: User bestätigt Scope → Ultrawork Phase 2 (IMPL) startet in Welle 0 mit Task 1.
