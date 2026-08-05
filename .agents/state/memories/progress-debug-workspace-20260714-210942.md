# Fortschritt — T2 Workspace-Mechanismus

## Status: completed

- Vertrag und Task Board gelesen.
- Serena MCP war nach zwei Versuchen nicht erreichbar (Timeout); gemäß Ausführungsprotokoll wurde für Memory-Operationen der direkte Fallback unter `.serena/memories/` verwendet. Serena CLI 1.5.3 war anschließend mit UTF-8 nutzbar.
- OpenCode 1.17.20: dokumentiertes `cwd`-Feld, aufgelöste Inline-Konfiguration und reale Client-Prozessprobe geprüft. Ergebnis: `client-context` ist mit globalem `cwd: "."` belastbar.
- AnythingLLM: lokal nicht installiert; offizielles Format, Release-Quellcode v1.15.0 und quellcodeäquivalente Transportproben geprüft. Ergebnis: keine Weitergabe eines aktiven Host-Fallordners; `unsupported_client_capability`.
- Gemeinsamer Office-MCP-Fallback auf `process.cwd()` identifiziert: unvalidierte Starts verbinden derzeit statt `workspace_unavailable` zu liefern.
- Produktivcode geändert: nein.
- Gesamtergebnis: FAIL, weil nicht jeder Client die geforderte Fähigkeit besitzt.
