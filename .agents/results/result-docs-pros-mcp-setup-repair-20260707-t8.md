Status: done

Summary:
- README bereinigt: SecureString-Pointer-Umweg ist nicht mehr bevorzugt; direkter stdin-Fluss mit `--client-secret-stdin` bleibt dokumentiert.
- OpenCode und AnythingLLM haben klare Neustart-/OAuth-Abschluss-Hinweise nach HubSpot- oder MCP-Aenderungen.
- `docs/CLI-MCP-COMMANDS.md` und `docs/MCP-CREDENTIALS.md` wurden entsprechend nachgezogen.
- Tracker `docs/plans/work/026-pros-mcp-setup-repair.md` markiert Task 8 als DONE und vermerkt generierte doc-ref-Drift.

Files changed:
- README.md
- docs/CLI-MCP-COMMANDS.md
- docs/MCP-CREDENTIALS.md
- docs/plans/work/026-pros-mcp-setup-repair.md

Verification:
- `oma docs verify --json` ausgefuehrt; Bericht enthielt weiterhin zahlreiche vorbestehende Broken-Refs ausserhalb des HubSpot-Scope.
- `oma docs sync HEAD~1..HEAD --json` ausgefuehrt; lieferte keine passendere Docs-Aktion fuer diesen Run.

Acceptance checklist:
- [x] README entfernt/entwertet SecureString-Pointer-Umwege.
- [x] Neustart/OAuth-Abschluss fuer OpenCode und AnythingLLM ist klar.
- [x] Keine Secrets werden im Doku-Fluss verlangt.
- [x] Vorherige Graph-Doku-Konsistenz unveraendert gelassen.
