# Ergebnis — T2 Workspace-Mechanismus

## Status: completed

## Verdict: FAIL

Nicht jeder Zielclient kann den aktiven Fallordner ohne persistierten Fallpfad oder `$PWD` an lokale Office-MCPs liefern. OpenCode besteht; AnythingLLM besitzt die erforderliche Client-Fähigkeit im geprüften Format/Release nicht.

## Zusammenfassung

| Client | Ergebnis | Vertragsstatus |
|---|---|---|
| OpenCode 1.17.20 | PASS | `client-context` unterstützt |
| AnythingLLM Desktop v1.15.0 (verfügbares Release; lokal nicht installiert) | FAIL | `unsupported_client_capability` |
| Office-MCP ohne validierten Kontext | FAIL (Ist-Zustand) | muss `workspace_unavailable` liefern |

## Konkrete Evidenz

### OpenCode — PASS

1. Lokal vorhanden: OpenCode CLI 1.17.20 und Desktop 1.17.20.
2. Das aktuelle OpenCode-Schema definiert für lokale MCPs `cwd` und dokumentiert: relative Pfade werden vom Workspace aus aufgelöst.
3. Eine ausschließlich per `OPENCODE_CONFIG_CONTENT` gesetzte, nicht persistierte Probe verwendete:

   ```json
   {
     "type": "local",
     "command": ["mcp-docx-local"],
     "cwd": ".",
     "enabled": true
   }
   ```

   `opencode debug config --pure` behielt `cwd: "."`; die Inline-Konfiguration enthielt weder den Fallpfad noch `$PWD`.
4. Reale OpenCode-Prozessprobe aus einem temporären Fallordner mit Leerzeichen:
   - CWD-Beobachter erhielt exakt den aktiven OpenCode-Workspace.
   - `mcp-docx-local`, `mcp-excel-local` und `mcp-powerpoint-local` meldeten jeweils `connected`.
   - Die normalen MCP-Listeneinträge der Probe enthielten nur die Befehlsnamen, keinen aufgelösten Fallpfad.
5. `packages/pros-cli/src/mcp-common.ts:42-58` setzt den Office-Runtime-Workspace derzeit auf `process.cwd()` beziehungsweise auf `--workspace`; damit erreicht das von OpenCode gesetzte Prozess-CWD die drei Office-Server.

Folgerung: Eine globale OpenCode-Konfiguration kann `cwd: "."` persistieren. Der aktive Workspace wird erst beim Client-Prozessstart aufgelöst; weder Fallpfad noch `$PWD` stehen in der globalen Datei.

### AnythingLLM — `unsupported_client_capability`

1. Lokale Realitätsprüfung: kein AnythingLLM-Befehl, kein laufender Prozess, kein Registry-Install und kein Storage-Verzeichnis vorhanden. Eine echte Desktop-Binärprobe war daher nicht möglich.
2. Offizielle Dokumentation für Desktop v1.15.0: `plugins/anythingllm_mcp_servers.json` unterstützt für stdio `command`, `args`, optional `env` und AnythingLLM-Metadaten. Ein Workspace-/CWD-Feld oder eine Laufzeitvariable für den aktiven Host-Ordner ist nicht dokumentiert.
3. Exakter Release-Quellcode v1.15.0, Commit `70e0d2eb1dcb08cbb18a44b927d94f8667f57a7f`, `server/utils/MCP/hypervisor/index.js`:
   - `#setupServerTransport` übergibt nur `command`, `args` und die gebaute Umgebung an `StdioClientTransport`.
   - `server.cwd` und ein AnythingLLM-Workspace werden nicht übergeben.
4. Die von v1.15.0 verwendete MCP-SDK-Version 1.24.3 setzt beim Spawn `cwd: this._serverParams.cwd`. Wegen der Auslassung im Hypervisor ist der Wert `undefined`; der Child-Prozess erbt das CWD des AnythingLLM-Hostprozesses.
5. Kontrollierte, quellcodeäquivalente Transportproben:
   - Trotz eines im Serverobjekt gesetzten Test-`cwd` auf den simulierten aktiven Fallordner erhielt der Child-Prozess das Host-Runtime-CWD; das Feld wurde wie im Hypervisor nicht weitergereicht.
   - Ein Argument `$PWD` kam beim Child-Prozess wörtlich als `$PWD` an (`shell: false`).
   - DOCX-, Excel- und PowerPoint-MCP verbanden sich im falschen Host-Runtime-CWD erfolgreich (3/5/3 Tools), statt `workspace_unavailable` zu melden.

Folgerung: AnythingLLM kann im geprüften Release keinen aktiven Host-Fallordner dynamisch in einen global definierten stdio-MCP-Prozess übertragen. Ein statischer absoluter Pfad wäre fallbezogene Persistenz; `$PWD` wird nicht expandiert; ein `cwd`-Feld wird vom Hypervisor nicht transportiert. Deshalb darf Pros für lokale Office-MCPs keinen irreführenden globalen AnythingLLM-Eintrag schreiben.

## Root Cause

- OpenCode besitzt eine explizite Workspace-relative `cwd`-Semantik.
- AnythingLLM besitzt nur eine globale statische MCP-Definition und reicht keinen aktiven Host-Fallordner an den stdio-Transport weiter.
- `packages/pros-cli/src/mcp-common.ts:45` behandelt jedes geerbte `process.cwd()` ungeprüft als gültigen Workspace. Dadurch können Office-MCPs aus einem Host-/Installationsverzeichnis starten, obwohl kein Fallworkspace verfügbar ist.

## Minimale Implementierungsvorgabe

1. **OpenCode:** Für DOCX, Excel und PowerPoint global `cwd: "."` schreiben; keinen absoluten `--workspace`-Wert und kein `$PWD` persistieren. CWD darf nur als Workspace akzeptiert werden, wenn der konfigurierte Modus die validierte OpenCode-`client-context`-Fähigkeit ausdrücklich auswählt; kein allgemeiner stiller CWD-Fallback.
2. **AnythingLLM:** Bei lokalen Office-Includes im Modus `client-context` `success: false`, `status: unsupported_client_capability` zurückgeben und die Konfiguration unverändert lassen. Für `explicit` ebenfalls keine Unterstützung behaupten, solange kein dokumentierter, nur für die aktuelle Invocation geltender Übergabekanal existiert.
3. **Office-MCP-Laufzeit:** Ohne absoluten expliziten Workspace oder ausdrücklich validierten Client-Kontext Dateizugriffe verweigern und strukturiert `workspace_unavailable` liefern. Die Änderung auf Office-Definitionen begrenzen oder per Workspace-Policy steuern, weil `runProsMcpServer` auch Microsoft Graph und QNAP Files bedient.
4. **Regressionstests:**
   - OpenCode-Eintrag enthält `cwd: "."`, aber keinen Fallpfad und kein `$PWD`.
   - Fallordner mit Leerzeichen wird beim realen OpenCode-Start zum Child-CWD; alle drei Office-MCPs verbinden.
   - AnythingLLM-Office-Konfiguration endet mit `unsupported_client_capability` und schreibt keine Datei/keinen Eintrag.
   - Office-MCP ohne validierten Kontext liefert `workspace_unavailable` statt Host-CWD zu verwenden.
   - Expliziter Workspace ist absolut, invocation-lokal und erscheint nie in globaler Client-Konfiguration.

## Ähnliche Muster / außerhalb T2

- Die aktuell installierte globale OpenCode-Konfiguration enthält bereits zwei legacy Office-Einträge mit einem fest persistierten Projektpfad und nicht vorhandenen Befehlsnamen. Das verletzt den neuen Vertrag und ist durch T3/T6 idempotent zu migrieren; T2 hat die Datei nicht verändert.
- Der gemeinsame `process.cwd()`-Fallback betrifft über `runProsMcpServer` neben den drei Office-Servern auch Microsoft Graph und QNAP Files. Eine pauschale Änderung ohne serverbezogene Policy wäre regressionsgefährlich.
- Eine echte AnythingLLM-Desktop-Smoke-Probe bleibt mangels lokaler Installation nicht ausführbar. Das begründet keinen erfundenen Supportmechanismus; ein späteres Release muss erneut gegen Format, Quellcode und Prozessstart validiert werden.

## Dateien geändert

- `.serena/memories/progress-debug-workspace-20260714-210942.md`
- `.serena/memories/result-debug-workspace-20260714-210942.md`
- Produktivcode: keiner
- Globale Client-Konfigurationen: unverändert

## Acceptance Criteria

- [x] Vertrag gelesen und Statuscodes angewendet.
- [x] OpenCode anhand installierter Version, Schema und realer Prozessprobe geprüft.
- [x] AnythingLLM anhand verfügbarem Releaseformat, exaktem Release-Quellcode und kontrollierter Transportprobe geprüft.
- [x] Kein Fallpfad und kein `$PWD` global persistiert.
- [x] Fehlende Fähigkeit als `unsupported_client_capability` dokumentiert.
- [x] Fehlendes Office-Workspace-Verhalten als `workspace_unavailable`-Vorgabe dokumentiert.
- [x] Ähnliche gemeinsame CWD-Fallback-Stelle gescannt.
- [x] Kein Produktivcode erstellt oder verändert.
