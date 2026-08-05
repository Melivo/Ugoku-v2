# Progress — QA Execution — ultrawork-20260627-pros-deterministic-setup-test

Status: in_progress
Phase: 2 IMPL / Step 5

## Turn 1

Action: Start sequentiellen QA-Ausführungsstrang gemaess genehmigtem Plan.

Context:
- PLAN_GATE passed.
- CP-02 wipe approved.
- CP-04 auth token via stdin not approved; if existing auth is invalid, block at CP-04 instead of asking for token in chat/stdin.
- CP-07 HubSpot client secret via terminal stdin approved.
- CP-09 OAuth browser flow approved.
- OS Credential Store wipe not approved.
- Target release: pros-v0.5.21.
- User reminder: update global `pros` to `@pro-select/pros-cli@0.5.21` before continuing setup checks.

Current task: T2 Bestehende Pros-managed MCP-Konfiguration sichern und wipen.

## T3 pros CLI Update Ergebnis

- Erster Install-Versuch mit `--registry https://git.leadt3ch.com/api/packages/leadt3ch/npm/` schlug fehl, weil oeffentliche Dependency `@modelcontextprotocol/sdk` dann faelschlich ueber Gitea aufgeloest wurde.
- Erfolgreicher Install-Versuch: `npm install -g @pro-select/pros-cli@0.5.21 --registry https://registry.npmjs.org/ --@pro-select:registry=https://git.leadt3ch.com/api/packages/leadt3ch/npm/`.
- Verifikation: `npm list -g @pro-select/pros-cli --depth=0` zeigt `@pro-select/pros-cli@0.5.21`.
- `pros --help` funktioniert.
- CP-03: PASS.

## T2 MCP-Konfigurationsbackup und Wipe Ergebnis

- Backup erstellt: `C:\Users\visimeos\AppData\Local\Temp\opencode\pros-mcp-backup-20260627-080059`.
- Gesichert: Pros managed state, OpenCode `opencode.jsonc`, AnythingLLM `anythingllm_mcp_servers.json`.
- OpenCode dry-run: Changed yes; Pros-managed HubSpot MCP entry kann sicher disabled werden.
- AnythingLLM dry-run: verweigert, da aktueller AnythingLLM-HubSpot-Eintrag nicht mehr Pros-managed Shape ist.
- OpenCode Wipe ausgefuehrt: `pros mcp disable opencode --include hubspot --force`; Status danach ready, keine Pros-managed MCP entries fuer opencode.
- AnythingLLM Wipe nicht ausgefuehrt/geschuetzt: `pros` verweigert Entfernung, damit Nicht-Pros-Konfiguration nicht veraendert wird.
- OS Credential Store wurde nicht gewiped; HubSpot Credential existiert weiter redacted.
- CP-02: PASS mit Hinweis, dass AnythingLLM keinen entfernbaren Pros-managed Eintrag hatte.

## T4 pros auth Ergebnis

- `pros auth status` meldet: Token configured: Yes; Registry access: OK; Release API access: OK.
- Kein Token wurde via stdin abgefragt oder gesetzt.
- CP-04: PASS.

## T5 frischer Fallordner Ergebnis

- Fallordner erstellt: `C:\Users\visimeos\AppData\Local\Temp\opencode\pros-e2e-case-20260627-0801`.
- `pros init` erfolgreich: initialized pros 0.5.21, release `pros-v0.5.21`, 197 Dateien installiert.
- `pros doctor` Ergebnis: `contact_support`.
- Doctor-Fehler: AnythingLLM Pros-managed HubSpot entry fehlt oder wurde durch non-Pros shape ersetzt.
- Bewertung: erwartet nach T2-Wipe/Schutzverhalten; CP-05 bleibt bedingt offen und soll nach T8-Konfiguration erneut geprueft werden.

## T6 Tool-Skills Ergebnis

- `pros tools` ausgefuehrt.
- `pros tools update` ausgefuehrt.
- Ergebnis fuer alle 7 globalen Tool-Skills: `foreign-conflict`; globale Skills existieren, sind aber nicht Pros-managed, daher wurden sie sicher nicht ueberschrieben.
- `pros tools update --dry-run` nachgeholt; Ergebnis ebenfalls `foreign-conflict` fuer alle 7 globalen Tool-Skills, keine Ueberschreibung.
- CP-06: PASS mit Hinweis auf nicht-Pros-managed vorhandene globale Skills.

## T7 HubSpot Credentials und MCP-Konfiguration

- Falscher Versuch `pros hubspot status`: CLI meldete `Unknown command: hubspot`; korrekter Befehl laut CLI/README ist `pros mcp hubspot credentials status`.
- `pros mcp hubspot credentials status`: Status ready; HubSpot MCP credentials vorhanden, secret redacted.
- `pros mcp configure opencode --include hubspot --dry-run`: ready, Changed yes.
- `pros mcp configure anythingllm --include hubspot --dry-run`: failed; bestehender non-Pros `hubspot`-Eintrag vorhanden, Ueberschreiben nur mit `--force` nach expliziter Sicherheitsbestaetigung.
- `pros mcp configure opencode --include hubspot`: ausgefuehrt.
- `pros mcp status opencode`: ready; Pros-managed HubSpot entry vorhanden, erwartete Shape, keine offensichtlichen Secrets in Config, OS Credential Store credential redacted vorhanden.
- AnythingLLM wurde noch nicht ueberschrieben, weil dies einen bestehenden non-Pros Eintrag ersetzen wuerde.
- CP-07: PASS fuer Credential-Readiness ohne Secret-Abfrage; Client Secret via stdin war nicht noetig, weil Credentials bereits ready waren.
- User bestaetigte explizit, den bestehenden non-Pros AnythingLLM `hubspot`-Eintrag zu ersetzen.
- `pros mcp configure anythingllm --include hubspot --force`: ausgefuehrt, Changed yes.
- `pros mcp status anythingllm`: ready; Pros-managed HubSpot entry vorhanden, erwartete Shape, keine offensichtlichen Secrets in Config, OS Credential Store credential redacted vorhanden.
- `pros doctor`: `safe_to_continue`; alle Checks bestanden.
- CP-05: nach erneuter Doctor-Pruefung PASS.
- CP-08: PASS fuer OpenCode und AnythingLLM Pros-managed HubSpot-Konfiguration ohne Secret-Leak in Client-Config.

## T8 Mistral/OpenCode README-Prompt Ergebnis

- `opencode run --model mistral/mistral-large-latest --print-logs <kanonischer README-Prompt>` aus Fallordner gestartet.
- Session: `ses_0f84de53cffej5Z9HR6TOFhva7`; Modell: `mistral/mistral-large-latest`; Skill/Workflow `/werkzeuge-mcp-einrichtung` wurde geladen.
- Mistral pruefte feste Pfade `C:\Program Files\opencode\opencode.exe` und `C:\Program Files\AnythingLLMDesktop\AnythingLLMDesktop.exe` sowie `Get-Process AnythingLLMDesktop`.
- Ergebnis: falscher Abbruch wegen angeblich fehlender OpenCode/AnythingLLM Voraussetzungen, obwohl `opencode` CLI verfuegbar ist und AnythingLLM Desktop bei Host-Inventar als installiert erkannt wurde.
- Bewertung: T8 gestartet, aber nicht erfolgreich abgeschlossen; Abweichung fuer T13/T14 erfassen. Workflow-Datei selbst enthaelt keine festen `Program Files`-Checks; Mistral hat diese Pruefungen eigenstaendig und falsch gewaehlt.

## T9 OpenCode HubSpot MCP Ergebnis

- `opencode mcp list` aus dem Fallordner ausgefuehrt.
- Ergebnis: `hubspot connected` mit Command `pros-mcp-hubspot-remote`.
- Weitere globale MCPs wurden ebenfalls gelistet; fuer T9 relevant ist HubSpot connected.
- CP-09: PASS; kein OAuth-Browser-Schritt noetig, offenbar war OAuth bereits gueltig/abgeschlossen.

## T10 AnythingLLM HubSpot MCP Ergebnis

- `pros mcp status anythingllm --probe`: statische Checks ready, Live-Probe nicht implementiert; erwartete Warnung.
- AnythingLLM war zunaechst nicht erreichbar; gestartet via `C:\Users\visimeos\AppData\Local\Programs\AnythingLLM\AnythingLLM.exe`.
- `/api/workspaces` auf `http://127.0.0.1:3001` erreichbar; Workspace `my-workspace` verwendet.
- Erster `@agent` WebSocket-Lauf startete Agent erfolgreich, listete aber zunaechst nicht HubSpot, sondern andere Tools; Backend-Log zeigte danach HubSpot-Attachments.
- Redaktionssichere Config-Shape: `SERVER hubspot COMMAND pros-mcp-hubspot-remote ARGS_COUNT 0`.
- Wrapper-Smoke `pros-mcp-hubspot-remote --help` startete erfolgreich gegen `https://mcp.hubspot.com/` und etablierte lokalen STDIO-Proxy; keine Secrets ausgegeben.
- Backend-Log `backend-2026-06-27.log` zeigt Attachments fuer `MCP::hubspot:search_crm_objects`, `MCP::hubspot:get_user_details` und weitere HubSpot-Tools.
- Zweiter `@agent` WebSocket-Lauf mit HubSpot-only Prompt: `stream-chat` lieferte `websocketUUID bcf95b41-ae80-4f0c-9083-104f579d872d`; WebSocket antwortete mit `hubspot-search_crm_objects`, `hubspot-get_user_details`, `hubspot-tool_guidance` u. a.; Summary `hubspot-tools-detected`.
- CP-10: PASS.

## T11 Isolierter Serena-Smoke-Test Ergebnis

- Wegwerfprojekt erstellt: `C:\Users\visimeos\AppData\Local\Temp\opencode\pros-serena-smoke-20260627-0822`.
- Eigene `.serena/project.yml` mit Projektname `pros-serena-smoke-20260627-0822` erstellt.
- `opencode mcp list` aus dem Wegwerfprojekt: Serena connected mit `C:/Users/visimeos/.local/bin/serena.exe start-mcp-server --context=ide --project-from-cwd`.
- Erster `serena project health-check` belegte Aktivierung des Wegwerfprojekts, scheiterte aber an fehlenden analysierbaren Dateien und zeigte zusaetzlich einen Windows-CP1252/Unicode-Ausgabebug fuer das Kreuzsymbol.
- Danach minimale `src/index.ts` im Wegwerfprojekt erstellt und Health-Check mit `PYTHONIOENCODING=utf-8`, `PYTHONUTF8=1` wiederholt.
- Zweiter Health-Check PASS: `GetSymbolsOverviewTool` fand `serenaSmoke`; `FindSymbolTool`, `FindReferencingSymbolsTool`, `SearchForPatternTool` liefen erfolgreich.
- Log: `C:\Users\visimeos\AppData\Local\Temp\opencode\pros-serena-smoke-20260627-0822\.serena\logs\health-checks\health_check_20260627-082116.log`.
- Serena hatte Temp-Projekte in `C:\Users\visimeos\.serena\serena_config.yml` registriert; genau diese zwei Temp-Eintraege wurden entfernt: `pros-e2e-case-20260627-0801` und `pros-serena-smoke-20260627-0822`.
- Backup vor Cleanup: `C:\Users\visimeos\AppData\Local\Temp\opencode\serena_config_before_temp_cleanup_20260627-0822.yml`.
- CP-11: PASS mit Hinweis auf entdeckten Serena-CP1252-Bug bei Unicode-Fehlerausgabe und auf notwendiges Cleanup automatisch registrierter Temp-Projekte.

## T12 Sicherheits- und Secret-Schutzchecks Ergebnis

- `pros doctor` im Fallordner: `safe_to_continue`, alle Checks bestanden.
- `pros mcp status opencode`: ready; Pros-managed HubSpot entry present; keine offensichtlichen Secrets in Client-Config; OS Credential Store credential redacted vorhanden.
- `pros mcp status anythingllm`: ready; Pros-managed HubSpot entry present; keine offensichtlichen Secrets in Client-Config; OS Credential Store credential redacted vorhanden.
- `pros mcp hubspot credentials status`: ready; secret redacted.
- Fallordner-Patternscan auf typische Secret-Indikatoren: `SECRET_SCAN no-pattern-hits`.
- CP-12: PASS.

## T13 README-/Runtime-Doku-Abgleich

- Reale Abweichung: Der Mistral/OpenCode-Lauf mit kanonischem README-Prompt brach falsch ab, weil Mistral feste `C:\Program Files\...`-Pfade pruefte statt `Get-Command opencode`, `%LOCALAPPDATA%\Programs\AnythingLLM\AnythingLLM.exe` und API-Probe zu nutzen.
- Ursache lag nicht als expliziter fester Pfad im Runtime-Workflow, aber der Workflow war zu wenig konkret und liess diese falsche Preflight-Interpretation zu.
- Fix umgesetzt in `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`: installationspfad-neutrale Preflight-Pruefungen explizit beschrieben.
- Fix umgesetzt in `README.md`: kanonischer Prompt nennt `Get-Command opencode`/`opencode --version` und warnt vor nur `C:\Program Files\...` fuer AnythingLLM.
- Verifikation: `node scripts/validate-runtime-files.js` PASS, 101 Dateien valide; nur bestehende nicht-blockierende Skill-Format-Warnungen.

## T14 Abweichungen und Release-Schritte

- Hauptabweichung: Der kanonische Mistral/OpenCode-Lauf startete korrekt und lud `/werkzeuge-mcp-einrichtung`, brach aber wegen falscher selbst gewaehler Festpfad-Preflightchecks ab.
- Wirkung: T8 ist `DONE_WITH_DEVIATION`; die eigentliche technische Einrichtung und Verifikation wurde anschliessend deterministisch durchgefuehrt und ist fuer OpenCode/AnythingLLM/Serena/Secret-Schutz bestanden.
- Fix im Source-Repo: `README.md` und `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md` wurden minimal ergaenzt, damit Agents installationspfad-neutrale Preflights nutzen.
- Offener Release-Schritt: Dieser Fix ist noch nicht in `@pro-select/pros-cli@0.5.21` bzw. `pros-v0.5.21` enthalten. Fuer Endnutzer braucht es einen neuen Release-Bump, Runtime-Bundle-Regeneration, Tag/Release und npm Publish.
- Weitere Hinweise: Serena CLI Health-Check hat einen Windows-CP1252/Unicode-Ausgabebug bei Fehlerausgabe gezeigt; AnythingLLM Live-Probe ist in `pros mcp status anythingllm --probe` noch nicht implementiert, der dokumentierte WebSocket-Flow funktioniert aber.
- CP-14: Abweichungen und naechste Release-Schritte erfasst; User gab Abschlussfreigabe mit "mache es"; Planstatus auf `Completed` gesetzt.
- Release-Follow-up: `docs(runtime): harden mcp setup preflight`, `chore(release): bump pros-cli to v0.5.22` und `chore(release): update runtime bundle for v0.5.22` wurden committed/gepusht.
- `pros-v0.5.22` wurde getaggt und als Gitea Release erstellt: `https://git.leadt3ch.com/leadt3ch/pro-select-harness/releases/tag/pros-v0.5.22`.
- `@pro-select/pros-cli@0.5.22` wurde published; `npm view` zeigt Version 0.5.22 und korrekte `bin`-Eintraege.
- Release-Assets `pros-runtime.apm`, `pros-runtime.apm.sha256`, `pros-manifest.json` wurden per Gitea MCP hochgeladen.
- Smoke nach Asset-Upload: globales `pros` 0.5.22 installiert; `pros init --release pros-v0.5.22` erfolgreich; `pros doctor` `safe_to_continue`; installierter Workflow enthaelt den installationspfad-neutralen Preflight-Hinweis.

## AnythingLLM API-Verifikationshinweis

- `docs/plans/work/018-pros-enduser-deterministic-setup-test.md` dokumentiert fuer CP-10: `/api/workspaces` liefert Workspace-Slug; `stream-chat` mit `@agent` liefert `agentInitWebsocketConnection` und `websocketUUID`; WebSocket `/api/agent-invocation/<uuid>` muss laufen; Agent muss `hubspot-*` Tools sehen.
- `README.md` bestaetigt: AnythingLLM Desktop muss lokal laufen; MCP-Tools muessen im Agent-Modus mit `@agent` genutzt werden; normale Chats sind kein zuverlaessiger MCP-Nachweis.
- `docs/references/anythingllm-mcp.md` bestaetigt AnythingLLM Desktop MCP-Unterstuetzung und Config-Datei `plugins/anythingllm_mcp_servers.json`.


## T1 Host-Inventar Ergebnis

- Node gefunden: v24.18.0.
- npm gefunden: 11.16.0.
- OpenCode CLI gefunden: 1.17.11.
- Globales `pros` gefunden, aktuell installiert: `@pro-select/pros-cli@0.5.20`.
- AnythingLLM Desktop installiert: 1.13.0 (Registry-Eintrag `AnythingLLM 1.13.0`).
- AnythingLLM-Prozess/Backend-Port nicht laufend/nicht nachgewiesen.
- `any` CLI fehlt.
- CP-01: pass with note; AnythingLLM muss fuer spaetere CP-10-Verifikation gestartet/erreichbar sein.

