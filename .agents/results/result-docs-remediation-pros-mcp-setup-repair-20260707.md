Status: done

Summary:
- README HubSpot-Snippet auf MaskInput + try/finally + Variable-Cleanup umgestellt.
- README Microsoft-Graph-Startbefehl auf `mcp-microsoft-graph` korrigiert.
- Tracker `docs/plans/work/026-pros-mcp-setup-repair.md` fuer Tasks 1-7 auf DONE und die Done-When-Checkliste auf erledigt gesetzt.

Files changed:
- README.md
- docs/plans/work/026-pros-mcp-setup-repair.md

Verification:
- `oma docs verify --json` -> scannedDocs 1021, totalRefs 5428, skippedCount 203, broken refs 331 (bestehende repo-weite Drift ausserhalb dieses Fix-Slices)
- `oma docs sync HEAD~1..HEAD --json` -> keine weitere passende Doc-Patch-Aktion fuer diesen kleinen Remediation-Slice
- Targeted grep checks confirmed `MaskInput`, `mcp-microsoft-graph`, and the tracker DONE state.

Acceptance criteria:
- [x] Unsafe visible HubSpot secret handling in README ersetzt
- [x] Microsoft Graph local start command in README korrigiert
- [x] Tracker Tasks 1-7 auf DONE gesetzt
- [x] Done-When-Checkliste auf erledigt gesetzt
- [x] Targeted verification checks ausgefuehrt
