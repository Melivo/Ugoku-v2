# Debug-Ergebnis: Serena globaler `--project`-Modus

## Status: failed

## Urteil

**FAIL** — Serena 1.5.3 unterstuetzt `--project` nur mit einem registrierten Projektnamen oder einem Projektstamm-Verzeichnis. Der im Plan geforderte zentrale YAML-Dateipfad `%USERPROFILE%/.config/pros/serena-project.yml` wird nicht als Projekt akzeptiert. Deshalb ist fuer den vereinbarten Modus `serena_global_project_unsupported` auszugeben. `--project-from-cwd` wurde weder verwendet noch als Fallback akzeptiert.

## Umgebung

- Windows 11 (`Windows-11-10.0.26200-SP0` laut Serena-Startlog)
- Executable: `C:\Users\phili\.local\bin\serena.exe`
- CLI-Version: `Serena 1.5.3`
- Vertrag: `.agents/results/api-contracts/pros-global-mcp-runtime-20260714.md`
- Aufgabe: Ultrawork Phase 2, T1

## Evidenz

### 1. Serena MCP im aktuellen Client

Zweimal ausgefuehrt:

```text
serena_initial_instructions()
```

Beide Ausgaben:

```text
MCP error -32001: Request timed out
```

Danach wurde entsprechend dem dokumentierten Windows-Recovery-Pfad nur fuer blockierte Operationen die installierte Serena-CLI verwendet. Zusaetzlich wurde ein eigenstaendiger Serena-MCP-Prozess ueber stdio mit echten JSON-RPC-Requests geprueft.

### 2. Installierte CLI und Hilfe

```powershell
Get-Command serena
serena --version
serena start-mcp-server --help
```

Relevante Ausgabe:

```text
Path    : C:\Users\phili\.local\bin\serena.exe
Serena 1.5.3
--project [PROJECT_NAME|PROJECT_PATH]
    Path or name of project to activate at startup.
--project-from-cwd
    Auto-detect project from current working directory ...
```

Das Flag existiert. Die Hilfe behauptet keinen YAML-Dateipfad, sondern Projektname oder Projektpfad.

### 3. Kontrollierte Startprobe mit gueltiger zentraler YAML-Datei

Die Probe erzeugte unter dem freigegebenen Temp-Bereich ein gueltiges Serena-Projekt:

```powershell
serena project create "C:\Users\phili\AppData\Local\Temp\opencode\serena-global-project-20260714-210942" --name "pros-global-probe-20260714-210942" --language typescript
```

Ausgabe:

```text
Generated project with languages {typescript} at C:\Users\phili\AppData\Local\Temp\opencode\serena-global-project-20260714-210942\.serena\project.yml.
```

Danach:

```powershell
'' | serena start-mcp-server --project "C:\Users\phili\AppData\Local\Temp\opencode\serena-global-project-20260714-210942\.serena\project.yml" --context ide --enable-web-dashboard false --open-web-dashboard false --log-level INFO
```

Relevante Ausgabe:

```text
ERROR ... Error activating project '...\.serena\project.yml' at startup:
Project '...\.serena\project.yml' not found: Not a valid project name or directory.
...
EXIT_CODE=0
```

Wichtig: Der Prozess faengt den Aktivierungsfehler ab, startet anschliessend einen MCP-Server ohne aktives Projekt und endet bei stdin-EOF trotzdem mit Exit-Code 0. Ein reiner Exit-Code-Test waere daher falsch-positiv.

Der installierte Code bestaetigt die Semantik in `serena/agent.py:1150-1160`: Zuerst wird ein registrierter Name gesucht, andernfalls nur `os.path.isdir(project_root_or_name)` akzeptiert. Eine YAML-Datei ist kein gueltiges Argument.

### 4. Gegenprobe mit zentralem Projektstamm-Verzeichnis

```powershell
'' | serena start-mcp-server --project "C:\Users\phili\AppData\Local\Temp\opencode\serena-global-project-20260714-210942" --context ide --enable-web-dashboard false --open-web-dashboard false --log-level INFO
```

Relevante Ausgabe:

```text
Found registered project 'pros-global-probe-20260714-210942' at path ...\serena-global-project-20260714-210942
Activating pros-global-probe-20260714-210942 at ...\serena-global-project-20260714-210942
Starting MCP server with 21 tools
EXIT_CODE=0
```

Damit ist der CLI-zulaessige Pfadtyp konkret belegt: ein absolutes Projektstamm-Verzeichnis. Eine angepasste zentrale Form waere beispielsweise:

```text
--project C:\Users\phili\.config\pros\serena-project
```

mit der Konfigurationsdatei an:

```text
C:\Users\phili\.config\pros\serena-project\.serena\project.yml
```

Dieser Verzeichnismodus ist jedoch **keine stillschweigende Ersetzung** fuer den derzeit vereinbarten Dateipfad `C:\Users\phili\.config\pros\serena-project.yml`; Plan und Sicherheitsgrenzen muessten vor seiner Verwendung explizit geaendert und erneut validiert werden.

### 5. Nicht-mutierender MCP-Tooltest

Ein eigenstaendiger stdio-MCP-Prozess wurde mit folgendem Projektstamm gestartet:

```text
serena start-mcp-server --project C:\Users\phili\Projects\pro-select-harness --context ide ...
```

JSON-RPC `initialize` antwortete erfolgreich. Danach wurde aufgerufen:

```json
{"method":"tools/call","params":{"name":"get_symbols_overview","arguments":{"relative_path":"packages/pros-cli/src/mcp-client-config.ts","depth":0}}}
```

Ergebnis:

```text
isError=false
Function: configureMcpClient, configureOpenCode, configureAnythingLlm, ...
Interface: McpCommandResult, McpConfigureOptions, ...
Variable: McpClient, McpInclude, McpStatusCode
EXIT_CODE=0
```

Der nicht-mutierende Toolpfad funktioniert, wenn `--project` ein Projektstamm-Verzeichnis erhaelt.

### 6. Kein impliziter CWD-Fallback

Aus einem Verzeichnis ohne `.serena/project.yml` und ohne `.git` wurde bewusst ohne `--project` und ohne `--project-from-cwd` gestartet. `get_current_config` antwortete:

```text
Error: No active project. Ask the user to provide the project path ...
EXIT_CODE=0
```

Serena aktivierte den CWD nicht stillschweigend. `--project-from-cwd` war in keiner Startprobe enthalten.

### 7. Aufraeumen

Die temporaere Projektregistrierung wurde aus der globalen Serena-Konfiguration entfernt und das Temp-Verzeichnis geloescht:

```text
REMOVED_PROJECT_REGISTRATION=pros-global-probe-20260714-210942
TEMP_PROJECT_REGISTERED=False
Test-Path <temp-project> => False
```

### 8. Aehnlichkeitsscan

`packages/pros-cli` enthaelt derzeit keinen Treffer fuer `--project`, `--project-from-cwd` oder `serena_global_project_unsupported`. In `runtime/pros` bestehen dagegen 21 Treffer, darunter ausgelieferte Empfehlungen fuer `--project-from-cwd` im Runtime-Manifest sowie in MCP-Einrichtungs-Workflow und Runtime-Skills. Diese Bestandsstellen wurden gemaess T1-Scope nicht geaendert; T5/T9/T11 muessen sie vor Auslieferung gegen den neuen Vertrag bereinigen. Sie sind **kein** zulaessiger Fallback fuer dieses Ergebnis.

## Root Cause

Der Plan behandelt `--project` als Pfad zu einer frei liegenden YAML-Konfigurationsdatei. Serena 1.5.3 interpretiert den Parameter dagegen als registrierten Projektnamen oder Verzeichnis. Der Prozess signalisiert einen ungueltigen YAML-Pfad zudem nur im Log und nicht ueber einen fehlerhaften Exit-Code. Dadurch reicht die geplante Exit-Code-0-Pruefung nicht aus.

## Minimale Implementierungsvorgabe fuer T3/T5

1. Vor dem Schreiben eines Serena-Client-Eintrags eine echte stdio-MCP-Startprobe mit dem exakt vorgesehenen zentralen Argument durchfuehren.
2. Nach `initialize` mindestens einen nicht-mutierenden Projekt-Toolaufruf ausfuehren und bestaetigen, dass das erwartete Projekt aktiv ist; Exit-Code 0 allein nicht akzeptieren.
3. Fuer den derzeit vereinbarten Pfad `%USERPROFILE%/.config/pros/serena-project.yml` keinen Eintrag schreiben und zurueckgeben:
   - `success: false`
   - Fehlercode: `serena_global_project_unsupported`
   - Hinweis: installierte Serena-Version akzeptiert nur Projektname oder Projektstamm-Verzeichnis.
4. Niemals auf `--project-from-cwd` ausweichen.
5. Kompatibilitaetsbehebung: entweder Serena auf eine nachweislich YAML-dateipfadfaehige Version aktualisieren oder Plan/Vertrag explizit auf einen zentralen Projektstamm-Verzeichnispfad umstellen und dessen Workspace-/Zugriffsgrenzen separat validieren.

## Dateien geaendert/erstellt

- `.serena/memories/progress-debug-serena-project-20260714-210942.md`
- `.serena/memories/result-debug-serena-project-20260714-210942.md`
- `.agents/results/result-debug-serena-project-20260714-210942.md`
- Kein Produktivcode geaendert.

## Akzeptanzkriterien

- [x] `--project` in der installierten CLI-Hilfe belegt.
- [ ] Zentraler YAML-Dateipfad aktiviert das Projekt erfolgreich — **nicht erfuellt; semantischer Aktivierungsfehler trotz Exit-Code 0**.
- [x] Nicht-mutierender MCP-Tooltest fuer den unterstuetzten Verzeichnispfad erfolgreich.
- [x] Kein impliziter oder expliziter `--project-from-cwd`-Fallback.
- [x] Konkreter CLI-zulaessiger Zentralpfadtyp und Windows-Beispiel dokumentiert.
- [x] Fehlerpfad `serena_global_project_unsupported` dokumentiert.
- [x] Aehnliche/veraltete `--project-from-cwd`-Muster gescannt und als Folgearbeit dokumentiert.
- [x] Temp- und globale Serena-Probeaenderungen vollstaendig aufgeraeumt.
- [x] Kein Produktivcode erstellt oder geaendert.
