# QA Smoke Result - pros-mcp-setup-repair Task 9

Session: `pros-mcp-setup-repair-20260707`
Task: P1 Task 9 - End-to-end Smoke-Run definieren und ausfuehren
Datum: 2026-07-07
Status: PASS

## Review Result: PASS

### CRITICAL
- Keine.

### HIGH
- Keine.

### MEDIUM
- Keine.

### LOW
- Keine.

## Summary

Der redaktionssichere Smoke-Run wurde lokal und ohne echte Provider-Secrets ausgefuehrt. Die produktionsnahen Live-Flows fuer Microsoft Graph OAuth-Abschluss, HubSpot OAuth/Credentials und QNAP NAS wurden mangels echter Zugangsdaten bewusst nicht simuliert; sie sind als externe Voraussetzungen dokumentiert. Ersatz-Evidenz kommt aus deterministischen lokalen Status-, Dry-run- und Test-Kommandos.

Wichtig: Die final gewertete Smoke-Runde lief mit isolierten Pfaden unter `C:\Users\phili\AppData\Local\Temp\opencode\pros smoke t9 20260707 isolated path with spaces`, inklusive Workspace- und Config-Pfaden mit Leerzeichen. Die OAuth-Ausgabe wurde fuer dieses Ergebnis redaktionell zusammengefasst; State/Session/Code-Challenge werden nicht in diesem Bericht wiedergegeben.

## Files Changed

- `.agents/results/result-qa-pros-mcp-setup-repair-20260707-t9.md` - dieses Smoke-Ergebnis.
- `docs/plans/work/026-pros-mcp-setup-repair.md` - Task 9 auf DONE gesetzt und Progress Note ergaenzt.
- Serena Memory `progress-qa-pros-mcp-setup-repair-20260707-t9.md` - Startstatus.
- Serena Memory `result-qa-pros-mcp-setup-repair-20260707-t9.md` - Ergebniszusammenfassung.

## Automated Checks First

Alle folgenden Checks wurden vor der manuellen Smoke-Auswertung ausgefuehrt:

| Command | Result |
|---|---:|
| `npm audit --audit-level=moderate` | PASS - `found 0 vulnerabilities` |
| `npm run lint` | PASS - Biome pruefte 68 Dateien |
| `npm run typecheck` | PASS |
| `npm test` | PASS - 27 Testdateien, 213 passed, 1 skipped |
| `npm run build` | PASS |

Relevante Test-Evidenz aus `npm test`: `packages/pros-cli/src/zip.test.ts` bestand inklusive Windows-APM/ZIP-Extraktionspfad; `packages/pros-cli/src/init.test.ts`, `microsoft-oauth.test.ts`, `microsoft-graph.test.ts`, `mcp-client-config.test.ts`, `mcp-qnap-assistant.test.ts` und `mcp-hubspot-remote.test.ts` bestanden ebenfalls.

## Smoke Commands and Results

### 1. Windows `pros init` / Pfad mit Leerzeichen

Isolierte Umgebung:

- Workspace: `...\pros smoke t9 20260707 isolated path with spaces\Case Workspace With Spaces`
- Fake Desktop: `...\Fake User Profile\Desktop`
- Fake Auth/Config-Pfade ueber `PROS_AUTH_DIR`, `PROS_DESKTOP_DIR`, `PROS_MCP_STATE_DIR`, `PROS_OPENCODE_CONFIG`, `PROS_ANYTHINGLLM_MCP_CONFIG`

| Command | Result |
|---|---:|
| `node packages/pros-cli/dist/cli.js init --workspace <path-with-spaces>` | PASS, Exit 0 |
| `node packages/pros-cli/dist/cli.js doctor --workspace <path-with-spaces>` | EXPECTED PARTIAL, Exit 1 wegen isoliert fehlendem `pros auth` Token |

Init-Evidenz:

- `.pros/state.json`: vorhanden
- `pros-runtime-manifest.md`: vorhanden
- `.agents/`: vorhanden
- `.serena/project.yml`: vorhanden
- Desktop assets: 3 Dateien im Fake Desktop installiert

`doctor` bestaetigte Runtime Config, Memory Structure, Installer State und OMA Config Check; `needs_auth` ist in der isolierten Auth-Umgebung erwartet und kein Produktcode-Blocker.

ZIP-/Release-Live-Download wurde nicht mit echtem Gitea/Pros-Release-Token ausgefuehrt. Ersatz-Evidenz: bestandener Windows-ZIP/APM-Extraktionstest plus bestandener lokaler Init-Smoke im Pfad mit Leerzeichen.

### 2. Microsoft Graph Setup-Status / Client-ID / Redirect

| Command | Result |
|---|---:|
| `node packages/pros-cli/dist/cli.js integrations graph status smoke-no-secret-t9` ohne `PROS_MICROSOFT_CLIENT_ID` | PASS/EXPECTED, Exit 1, Status `needs-auth`, Meldung verweist auf fehlende Client ID und sagt, MCP-Client-Konfiguration sei nicht Ursache |
| `node packages/pros-cli/dist/cli.js integrations auth microsoft-graph start` ohne Client ID | PASS/EXPECTED, Exit 1, `Missing PROS_MICROSOFT_CLIENT_ID.` |
| gleiches Graph-Statuskommando mit Dummy-Client-ID `00000000-0000-0000-0000-000000000000` | PASS/EXPECTED, Exit 1, fehlendes OS-Credential statt Client-ID-Fehler |
| `integrations auth microsoft-graph start` mit Dummy-Client-ID und Redirect `http://localhost:53682/oauth/microsoft/callback` | PASS, Exit 0, OAuth URL vorbereitet, Redirect/Tenant/Scopes angezeigt, PKCE-Verifier nur lokal in temporarer Pros-Session-State abgelegt |

Echte OAuth-Anmeldung und Token-Austausch: NOT RUN, externe Voraussetzung echte Azure App Registration + Nutzerzustimmung/Admin Consent.

### 3. QNAP Tokenstatus / Empty stdin / Credential Target

| Command | Result |
|---|---:|
| `node packages/pros-cli/dist/cli.js mcp qnap token status` | PASS/EXPECTED, Exit 1, Status `needs_credential`, Target `pros:qnap:mcp-assistant` |
| `<empty stdin> | node packages/pros-cli/dist/cli.js mcp qnap token set --stdin` | PASS/EXPECTED, Exit 1, klare Empty-stdin-Meldung, Target `pros:qnap:mcp-assistant`, kein Token geschrieben |

QNAP Live-Smoke gegen NAS: NOT RUN, externe Voraussetzung interner QNAP Assistant Token und NAS-seitige Read-only-/Feature-Kontrollen. Keine Token wurden erzeugt, geraten oder ausgegeben.

### 4. HubSpot Credential/Status/Config Guidance

| Command | Result |
|---|---:|
| `node packages/pros-cli/dist/cli.js mcp hubspot credentials status` | PASS/EXPECTED, Exit 1, Status `needs_credential`, keine Secret-Ausgabe |
| `node packages/pros-cli/dist/cli.js mcp configure opencode --include hubspot --dry-run` | PASS/EXPECTED, Exit 1, fordert `pros mcp hubspot credentials set --client-id <id> --client-secret-stdin` |
| `node packages/pros-cli/dist/cli.js mcp configure anythingllm --include hubspot --dry-run` | PASS/EXPECTED, Exit 1, gleiche redaktionssichere Guidance |

HubSpot Live-OAuth und echte Credentials: NOT RUN, externe Voraussetzung echte HubSpot MCP Auth App + Client ID/Secret via stdin + Browser-OAuth.

### 5. MCP Config Dry-runs/Status OpenCode und AnythingLLM

| Command | Result |
|---|---:|
| `node packages/pros-cli/dist/cli.js mcp status opencode` | PASS, Exit 0, keine Pros-managed Clients in isolierter State-Datei, keine Secrets gelesen/gedruckt |
| `node packages/pros-cli/dist/cli.js mcp status anythingllm` | PASS, Exit 0, keine Pros-managed Clients in isolierter State-Datei, keine Secrets gelesen/gedruckt |
| `node packages/pros-cli/dist/cli.js mcp configure opencode --include microsoft-graph --dry-run` | PASS, Exit 0, `Dry run: yes`, `Changed: yes`, Config-Pfad mit Leerzeichen |
| `node packages/pros-cli/dist/cli.js mcp configure anythingllm --include microsoft-graph --dry-run` | PASS, Exit 0, `Dry run: yes`, `Changed: yes`, Config-Pfad mit Leerzeichen |
| `node packages/pros-cli/dist/cli.js mcp configure opencode --include qnap-mcp-assistant --dry-run` | PASS/EXPECTED, Exit 1, fehlender QNAP-Token mit Target-Guidance |
| `node packages/pros-cli/dist/cli.js mcp configure anythingllm --include qnap-mcp-assistant --dry-run` | PASS/EXPECTED, Exit 1, fehlender QNAP-Token mit Target-Guidance |

Dry-run-No-write-Evidenz nach den Dry-runs:

- OpenCode Config-Datei existiert nicht: `False`
- AnythingLLM Config-Datei existiert nicht: `False`
- MCP managed-state Datei existiert nicht: `False`

Damit blieb die No-Secret-Invariante erhalten: Status/Dry-runs druckten keine Tokens/Secrets und schrieben keine Client-Konfiguration.

## Blocker / External Prerequisites

Keine Code-Blocker fuer Task 9 gefunden. Folgende Live-Anteile bleiben externe Voraussetzungen:

1. Authentifizierter Release-ZIP-Download fuer echtes `pros init` aus Gitea/Forgejo Release-Artefakten.
2. Microsoft Graph OAuth-Abschluss mit echter Azure App Registration und Admin/User Consent.
3. QNAP NAS Live-Initialisierung mit internem QNAP Assistant Token und NAS-seitigen Safety Gates.
4. HubSpot Live-OAuth mit echter MCP Auth App und Credentials via stdin.

## Acceptance Criteria Checklist

- [x] Windows-Smoke deckt `pros init`, Graph-Setup-Status, QNAP-Tokenstatus, HubSpot-Status und MCP-Config-Dry-runs ab.
- [x] Smoke-Ergebnis ist redaktionssicher dokumentiert; keine echten Tokens/Secrets enthalten.
- [x] Fehlschlaege/Not-runs sind als erwartete externe Voraussetzungen mit Root-Cause-Hinweis dokumentiert.
- [x] Keine Secrets oder echten Tokens ausgegeben.
