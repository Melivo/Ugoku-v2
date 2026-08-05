# Pros MCP/Setup Root-Cause-Untersuchung

Datum: 2026-07-07

## Rahmen

- Sprache: `.agents/oma-config.yaml` setzt `language: de`.
- Vendor-Detection: OpenCode Runtime; Debug-Zielvendor ebenfalls OpenCode.
- L1-Session: `debug-pros-mcp-setup-20260707`.
- L1-Checkpoint: `decision.made` fuer `debug.root-cause` emittiert und verifiziert.
- Umfang: Ursachenforschung only; keine Loesung entwickelt, keine Umsetzung vorgenommen.

## Eingangsberichte

- `C:\Users\phili\Downloads\pros-init-debug-bericht.md`
- `C:\Users\phili\Downloads\Microsoft_Graph_Debug_Bericht.md`
- `C:\Users\phili\Downloads\Microsoft_Graph_MCP_Einrichtung_Bericht.md`
- `C:\Users\phili\Downloads\QNAP_MCP_Debug_Bericht.md`
- `C:\Users\phili\Downloads\HubSpot_MCP_Einrichtung_Bericht.md`

## Symptome

- `pros init` meldete im Endnutzer-Workspace mit Leerzeichen im Pfad `Manifest verification failed` und viele `File missing: ...`-Eintraege.
- Microsoft Graph OAuth scheiterte mit `AADSTS700016` fuer Client-ID `c7e16106-5843-4e98-82b0-cf76d9c2bcea` im Tenant `Pro Select`.
- `pros mcp qnap token set --stdin` wirkte haengend; `pros mcp qnap token status` meldete weiter `needs_credential`.
- HubSpot war laut Bericht weitgehend erfolgreich; verbleibend waren Neustart/OAuth-Abschluss/Doku-Hinweise, keine bestaetigte Code-Fehlfunktion.

## MCP-Codeanalyse

- `pros init` Pfad: `packages/pros-cli/src/cli.ts` `runCommand` -> `packages/pros-cli/src/init.ts` `initWorkspace` -> `extractZip` -> `packages/pros-cli/src/zip.ts` `extract` -> `verifyManifest`.
- `zip.extract` ruft auf Windows `powershell -Command "& { param($archive, $destination) Expand-Archive ... }"` mit Pfaden als nachgelagerten Argumenten auf.
- Der Bericht zeigt, dass bei Zielpfaden mit Leerzeichen PowerShell Exit-Code 0 lieferte, aber das Ziel leer blieb.
- `verifyManifest` meldet `File missing` nur, weil nach dem fehlerhaften Entpacken im `extracted`-Ordner die erwarteten Manifest-Dateien fehlen. Das ist Symptom, nicht Root Cause.
- Microsoft Graph Pfad: `cli.ts` `runCommand` -> `microsoft-oauth.ts` `createMicrosoftOAuthStart` -> `buildMicrosoftAuthorizationUrl`.
- `buildMicrosoftAuthorizationUrl` verwendet `process.env.PROS_MICROSOFT_CLIENT_ID`; `AADSTS700016` bedeutet, dass Microsoft diese Client-ID im angesprochenen Tenant nicht findet.
- Zusaetzlicher Graph-Dokudrift-Befund: Berichte nennen Redirect `http://localhost:19876/auth/microsoft/callback`, der aktuelle Code nutzt default `http://localhost:53682/oauth/microsoft/callback`. Das erklaert nicht `AADSTS700016`, ist aber ein separates Setup-Risiko.
- QNAP Pfad: `cli.ts` `runCommand` -> `readTokenFromStdin` -> `mcp-client-config.ts` `setQnapMcpAssistantToken` -> `credential-store.ts` `setCredential`.
- `readTokenFromStdin` liest `process.stdin` bis EOF. Bei interaktiver Eingabe ohne Pipe/EOF wirkt der Befehl erwartbar haengend; das ist stdin-Bediensemantik, nicht ein nachgewiesener Credential-Store-Deadlock.
- QNAP Credential Target ist fest `pros:qnap:mcp-assistant`; manuelles Speichern unter `https://nasproselect.myqnapcloud.com:8443` wird von `hasCredential/getCredential` nicht gefunden.

## Root Causes

1. `pros init`: Windows-spezifische PowerShell-Argumentbindung beim `Expand-Archive`-Aufruf in `packages/pros-cli/src/zip.ts` bei Zielpfaden mit Leerzeichen. Die Manifestfehler sind Folge eines leeren Extraktionsziels.
2. Microsoft Graph: Verwendete Azure AD Client-ID existiert im Tenant `Pro Select` nicht oder ist nicht fuer diesen Tenant erreichbar. Separat besteht Redirect-URI-Dokudrift zwischen Bericht und aktuellem Code.
3. QNAP: Missverstaendliche/pipe-abhaengige stdin-Nutzung plus Credential-Target-Mismatch bei manueller Ablage. Pros sucht `pros:qnap:mcp-assistant`, nicht die NAS-URL.
4. HubSpot: Kein bestaetigter Defekt; Bericht zeigt erfolgreiche Credential- und Client-Konfiguration mit ausstehenden Laufzeit-/Doku-Schritten.

## Similar Pattern Scan

- PowerShell-Aufrufe in `packages/pros-cli/src`: `credential-store.ts` nutzt `powershell.exe -NonInteractive` mit JSON-stdin; `zip.ts` nutzt PowerShell fuer ZIP-Listing und `Expand-Archive`. Der fuer `pros init` relevante gleiche Fehlerklassentreffer ist `zip.ts` `Expand-Archive`.
- `readTokenFromStdin` wird fuer Gitea auth token, HubSpot client secret und QNAP token wiederverwendet. Die gleiche EOF-Bediensemantik betrifft alle stdin-basierten Secret-Kommandos.
- Feste Credential Targets existieren fuer HubSpot und QNAP. QNAP-Bericht zeigt konkret manuelle Ablage unter falschem Target; HubSpot-Bericht zeigt hingegen erfolgreiche Speicherung ueber CLI.

## Dateien Geaendert

- Keine Quellcode-Aenderungen.
- Dokumentationsartefakt: `.agents/results/bugs/pros-mcp-setup-root-cause-20260707.md`.

## Regressionstest

- Kein Regressionstest geschrieben, weil ausdruecklich nur Ursachenforschung und noch keine Loesungsentwicklung/Umsetzung angefordert wurde.
