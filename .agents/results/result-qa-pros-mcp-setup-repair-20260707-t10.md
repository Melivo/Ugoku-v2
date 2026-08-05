# QA Release-/Rollback-Check - pros-mcp-setup-repair Task 10

Session: `pros-mcp-setup-repair-20260707`
Task: P2 Task 10 - Release-/Rollback-Check vorbereiten
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

Der Release-/Rollback-Check ist vorbereitet. Betroffene Version ist `@pro-select/pros-cli@0.5.30` mit Release-Tag `pros-v0.5.30`, bestaetigt durch `packages/pros-cli/package.json:3`, `package-lock.json:2888` und den erfolgreichen `npm run release:dry-run`.

Task 9 ist als Smoke-PASS verwertbar: lokale Checks, Windows-Pfad-mit-Leerzeichen-Init, Graph/QNAP/HubSpot Status- und Dry-run-Evidenz wurden ohne echte Secrets dokumentiert (`.agents/results/result-qa-pros-mcp-setup-repair-20260707-t9.md:35-45`, `:51-123`, `:125-139`). Die verbleibenden Live-Flows bleiben externe manuelle Verifikation.

## Files Changed

- `.agents/results/result-qa-pros-mcp-setup-repair-20260707-t10.md` - dieser Release-/Rollback-Check.
- `docs/plans/work/026-pros-mcp-setup-repair.md` - Task 10 auf DONE gesetzt und Progress Note ergaenzt.
- Serena Memory `progress-qa-pros-mcp-setup-repair-20260707-t10.md` - Startstatus.
- Serena Memory `result-qa-pros-mcp-setup-repair-20260707-t10.md` - Ergebniszusammenfassung.

## Automated Checks First

| Command | Result |
|---|---:|
| `npm audit --audit-level=moderate` | PASS - `found 0 vulnerabilities` |
| `npm run lint` | PASS - Biome pruefte 68 Dateien |
| `npm run typecheck` | PASS |
| `npm run release:dry-run` | PASS - Version `0.5.30`, Tag `pros-v0.5.30`, Dry-run ohne Release-Seiteneffekte |

## Gepruefte Release-Basis

- CLI-Version: `@pro-select/pros-cli` ist `0.5.30` (`packages/pros-cli/package.json:2-3`); Lockfile ist aligned (`package-lock.json:2886-2888`).
- Release-Tag: `scripts/release.js` bildet `pros-v${version}` (`scripts/release.js:432-435`) und validiert SemVer/Tag (`scripts/release.js:438-439`).
- Release-Artefakte: aktueller Workflow baut `pros-runtime.apm`, `pros-runtime.apm.sha256` und `pros-manifest.json` (`.gitea/workflows/release.yaml:143-179`, `:283-294`). Das APM-Bundle ist ZIP-kompatibel; die manuelle Verifikation unten nennt deshalb bewusst `Release-ZIP/APM Init`.
- Release-Gate: Tag-Version muss zur Package-Version passen (`.gitea/workflows/release.yaml:36-51`), danach laufen Preflight und `npm pack --dry-run` (`.gitea/workflows/release.yaml:59-64`).
- Runtime-Schutz: Workflow prueft, dass die Runtime `pros-config.yaml` enthaelt und keine `oma-config.yaml`/legacy `apm.yml` einschliesst (`.gitea/workflows/release.yaml:123-141`).
- Installer-Schutz: `pros init` laedt Release-Assets, prueft SHA256 und Manifest-Hashes, legt bei Nicht-`--force` Backups an und schreibt `.pros/state.json` erst nach erfolgreicher Installation (`packages/pros-cli/src/init.ts:610-640`, `:663-677`, `:724-741`).
- Pinning/Rollback-Faehigkeit: `pros update --release <tag>` nutzt den angegebenen Release-Tag und fuehrt die Update-Installation ueber dieselbe verifizierende Init-Logik aus (`packages/pros-cli/src/update.ts:56-83`).

## Zielgerichtete Grep-/Konsistenzchecks

| Check | Result |
|---|---:|
| Tracker Task 10 Status in `docs/plans/work/026-pros-mcp-setup-repair.md` | PASS - `DONE` in Zeile 54 |
| Tracker Progress Note fuer Task 10 | PASS - Ergebnisdatei verlinkt in Zeile 78 |
| Secret-/ID-Muster im Ergebnisartefakt (GUID/Auth-Header/Token-Zuweisung/Client-Secret-Zuweisung) | PASS - keine Treffer |
| Akzeptanzbegriffe im Ergebnisartefakt (`0.5.30`, `pros-v0.5.30`, Graph OAuth, QNAP NAS, HubSpot OAuth, Release-ZIP/APM, Rollback) | PASS - vorhanden |

## Release Notes Draft

### pros CLI `0.5.30` / Tag `pros-v0.5.30`

**Highlights**

- Stabilisiert `pros init` fuer Windows-Fallordner mit Leerzeichen im Pfad; Smoke-Evidenz bestaetigt erfolgreiche Installation in isoliertem Pfad mit Leerzeichen.
- Konsolidiert Microsoft-Graph-Setup-Hinweise fuer Client ID, optionalen Tenant und Redirect URI; OAuth-PKCE-Start gibt keine Verifier/Tokens aus.
- Vereinheitlicht QNAP MCP Assistant Credential-Target und stdin-UX; leere stdin-Eingabe scheitert redaktionssicher ohne Token-Schreibvorgang.
- Validiert OpenCode-/AnythingLLM-MCP-Konfiguration als secret-free und idempotent; QNAP/HubSpot-Provider-Secrets bleiben im OS Credential Store.
- Klaert HubSpot MCP Wrapper-Flow fuer OpenCode und AnythingLLM inklusive Credentials via stdin, Client-Neustart und OAuth/Probe-Nachkontrolle.

**Artefakte**

- `pros-runtime.apm`
- `pros-runtime.apm.sha256`
- `pros-manifest.json`

**Bekannte externe Release-Checks vor Freigabe**

- Microsoft Graph OAuth-Ende-zu-Ende mit echter Azure App Registration und Consent.
- QNAP NAS Live-Initialisierung mit internem Assistant Token und NAS-seitigen Read-only-/Feature-Gates.
- HubSpot OAuth-Ende-zu-Ende mit echter HubSpot MCP Auth App und Credentials via stdin.
- Authentifizierter `pros init --release pros-v0.5.30` aus privatem Gitea/Forgejo Release-Asset in sauberem Windows-Fallordner.

## Manuelle Verifikation fuer externe Live-Flows

Keine echten IDs, Tokens, Tenantnamen, DriveItem-IDs, NAS-Pfade oder CRM-Datensaetze in Tickets/Chat/Logs kopieren. Platzhalter wie `<client-id>`, `<case-path>`, `<previous-tag>` beibehalten.

### 1. Release-ZIP/APM Init

1. Auf einem frischen Windows-Testprofil CLI aus privater Registry installieren: `npm install -g @pro-select/pros-cli@0.5.30`.
2. Release-Zugriff nur lokal setzen: `pros auth token set --stdin`; Token nicht in argv, Chat oder Logs schreiben.
3. Sauberen Fallordner mit Leerzeichen anlegen, z. B. `<case-path-with-spaces>`.
4. `pros auth status` ausfuehren und nur redaktionelle Statuskategorie dokumentieren.
5. `pros init --release pros-v0.5.30 --workspace "<case-path-with-spaces>"` ausfuehren.
6. `pros doctor --workspace "<case-path-with-spaces>"` ausfuehren.
7. Erwartung: `.pros/state.json` zeigt `installedVersion: 0.5.30` und `releaseTag: pros-v0.5.30`; `pros-runtime-manifest.md`, `.agents/pros-config.yaml`, `.serena/project.yml` und `pros-Hilfe` sind vorhanden; keine Secret-Werte in Fallordnerdateien.
8. Release-Asset-Konsistenz pruefen: privates Release enthaelt die unter "Artefakte" genannten Dateien; das APM-Bundle muss checksum-/manifest-verifiziert installiert werden.

### 2. Microsoft Graph OAuth

1. Echte Azure App Registration durch IT/Admin bereitstellen; `PROS_MICROSOFT_CLIENT_ID=<client-id>` setzen, optional `PROS_MICROSOFT_TENANT_ID=<tenant>` und `PROS_MICROSOFT_REDIRECT_URI=http://localhost:53682/oauth/microsoft/callback`.
2. `pros integrations auth microsoft-graph start` ausfuehren, Browser-OAuth abschliessen und Consent-Status dokumentieren.
3. `pros integrations graph status` ausfuehren; erwartete Readiness ist `ready-read` oder `ready-business-write-safe` je nach Consent.
4. Nicht-mutierende Reads pruefen: `mail search`, `calendar list`, `files search` mit harmlosen Testbegriffen/Zeitraeumen.
5. MCP-Wrapper-Write-Pfade nur mit Testdaten, explizitem `confirmationStatus: "CONFIRMED"` und ohne echte personenbezogene Inhalte pruefen.
6. Verifizieren: Tokens nur OS Credential Store; keine Tokens in MCP-Client-Dateien, `.pros`, `.agents`, `.serena`, Logs oder Release-Artefakten.

Referenz: Graph-Setup und Scopes sind in `docs/CLI-MCP-COMMANDS.md:100-128` und `docs/MCP-CREDENTIALS.md:123-144` beschrieben.

### 3. QNAP NAS / QNAP MCP Assistant

1. Internen QNAP Assistant Token ausserhalb von Chat/Repo bereitstellen und nur via `pros mcp qnap token set --stdin` speichern.
2. `pros mcp qnap token status` ausfuehren; erwartete Kategorie: credential vorhanden/ready, ohne Token-Ausgabe.
3. Vor Client-Write: `pros mcp configure opencode --include qnap-mcp-assistant --dry-run` und/oder `pros mcp configure anythingllm --include qnap-mcp-assistant --dry-run` ausfuehren.
4. Nach Freigabe ohne `--dry-run` konfigurieren, Desktop-Client neu starten und `pros mcp status <client> --probe` nur in freigegebener Umgebung ausfuehren.
5. Im MCP-Client ausschliesslich nicht-mutierende NAS-Tools testen; Upload/Overwrite/Delete/Admin-Funktionen muessen durch NAS-seitige Read-only-/Feature-Kontrollen blockiert sein, sofern kein separates Preview/Approval-Modell existiert.
6. Keine NAS-Pfade, Share-Namen, Tokens, Sessions oder Cookies in Ergebnisartefakte kopieren.

Referenz: QNAP Boundary ist in `docs/CLI-MCP-COMMANDS.md:163-170` und `docs/MCP-CREDENTIALS.md:161-178` beschrieben.

### 4. HubSpot OAuth / Remote MCP Wrapper

1. HubSpot OAuth-App und Redirect `http://127.0.0.1:19876/oauth/callback` durch Admin bestaetigen.
2. Credentials secret-free setzen: `pros mcp hubspot credentials set --client-id <id> --client-secret-stdin`.
3. `pros mcp hubspot credentials status` ausfuehren; nur redaktionelle Statuskategorie dokumentieren.
4. `pros mcp configure opencode --include hubspot --dry-run` und/oder `pros mcp configure anythingllm --include hubspot --dry-run` ausfuehren; danach mit Freigabe ohne `--dry-run`.
5. OpenCode Desktop/AnythingLLM Desktop neu starten, OAuth im Browser abschliessen und `pros mcp status <client> --probe` ausfuehren.
6. Nicht-mutierenden HubSpot-Toolaufruf verwenden, z. B. Nutzer-/Account-Details, aber keine echten Portal-IDs oder Datensatz-IDs dokumentieren.
7. Verifizieren: Client-Konfiguration enthaelt nur `pros-mcp-hubspot-remote`; keine `clientSecret`, keine rohe Remote-URL mit Secrets, keine OAuth Tokens.

Referenz: HubSpot-Flow und Neustartanforderung sind in `docs/MCP-CREDENTIALS.md:35-69` und `docs/CLI-MCP-COMMANDS.md:195-204` beschrieben.

## Rollback-Hinweise fuer Endnutzer

### Vor jeder Live-Aenderung

- `pros doctor --workspace "<case-path>"` ausfuehren und Statuskategorie notieren.
- Bei MCP-Client-Konfiguration zuerst `--dry-run` nutzen; keine Datei aendern, bevor der angezeigte Zielpfad plausibel ist.
- Kein `--force` verwenden, ausser Support fordert es explizit an; ohne `--force` legt `pros init/update` Backups unter `.pros/backups/<timestamp>` an (`packages/pros-cli/src/init.ts:539-585`, `:673-677`).

### Runtime-/CLI-Rollback

1. Letzten funktionierenden Tag aus `.pros/state.json` oder Support-Notizen ermitteln, z. B. `<previous-tag>`.
2. Trockenlauf: `pros update --release <previous-tag> --workspace "<case-path>" --dry-run`.
3. Wenn der Zieltag stimmt: `pros update --release <previous-tag> --workspace "<case-path>"`.
4. Danach `pros doctor --workspace "<case-path>"` und ggf. einen nicht-mutierenden Smoke (`pros mcp status`, Graph/QNAP/HubSpot Status) ausfuehren.
5. Wenn Update fehlschlaegt: keine manuelle Loeschung; `.pros/backups/<timestamp>` sichern und Support einschalten.

### MCP-/Provider-Rollback

- OpenCode/AnythingLLM: erst `pros mcp disable <client> --include <server> --dry-run`, dann nach Freigabe ohne `--dry-run`; fremde MCP-Eintraege muessen erhalten bleiben.
- HubSpot: bei Credential-Problem `pros mcp hubspot credentials clear --force`, danach Desktop-Client neu starten und Credentials neu per stdin setzen.
- QNAP: bei Token-Problem `pros mcp qnap token clear --force`, danach neuen Token nur per stdin setzen; NAS-seitige Berechtigungen durch Admin pruefen lassen.
- Microsoft Graph: bei falscher App/Tenant/Consent OS-Credential entfernen bzw. Consent durch Admin/User widerrufen lassen, danach OAuth neu starten. `AADSTS700016` als App-/Tenant-/Client-ID-Problem behandeln, nicht als MCP-Client-Konfigurationsfehler.
- Nach jedem Provider-Rollback Desktop-Client komplett neu starten und nur redaktionelle Statuskategorien dokumentieren.

## Acceptance Criteria Checklist

- [x] Betroffene CLI-Version und Release-Notizen sind vorbereitet.
- [x] Manuelle Verifikation ist beschrieben, inklusive Graph OAuth, QNAP NAS, HubSpot OAuth, Release-ZIP/APM Init.
- [x] Rollback-Hinweise fuer Endnutzer sind dokumentiert.
- [x] Keine Secrets oder echten IDs/Tokens enthalten; nur Platzhalter und Statuskategorien.
