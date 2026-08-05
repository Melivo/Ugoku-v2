# Progress Backend T1

Status: gestartet
Session: pros-mcp-setup-repair-20260707
Task: P0 Task 1 - Windows-`pros init`-Extraktion reparieren

Scope:
- Bearbeitbar: `packages/pros-cli/src/zip.ts`, relevante ZIP/Init-Tests, minimale Fixtures.
- Nicht bearbeiten: Microsoft Graph Dateien, QNAP Credential/stdin Dateien, Docs.

Akzeptanz:
1. Workspace-Pfade mit Leerzeichen extrahieren korrekt auf Windows.
2. Leere Extraktion fuehrt zu klarer Fehlermeldung vor Manifest-Folgefehlern.
3. Regressionstest deckt Leerzeichen-Pfad oder fehlerhaften Windows-Extractor-Aufruf ab.

Naechste Schritte:
- Stack anhand Projektdateien erkennen.
- `zip.ts` symbolisch analysieren (`extract`, `listExtractedEntries`, `verifyManifest`).
- Minimalen Root-Cause-Fix implementieren und scoped Tests ausfuehren.
