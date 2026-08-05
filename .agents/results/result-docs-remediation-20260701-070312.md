# Docs/Runtime Remediation Result - Session 20260701-070312

## Status
done

## Summary
- Runtime- und Projection-Doku auf kanonische MCP-Namen synchronisiert.
- Legacy-Duplikat fuer Microsoft Graph entfernt.
- `office-files`-Bridge durch `Local PowerPoint` und `Local Excel` ersetzt.
- Workflow- und Skill-Referenzen auf `mcp-microsoft-graph`, `mcp-docx-local`, `mcp-powerpoint-local`, `mcp-excel-local` aktualisiert.

## Files changed
- `runtime/pros/pros-runtime-manifest.md`
- `build/runtime-projection/pros-runtime-manifest.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`
- `build/runtime-projection/.agents/workflows/werkzeuge-mcp-einrichtung.md`
- `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md`
- `build/runtime-projection/.agents/skills/mcp-config-sync-pros/SKILL.md`

## Verification
- Zielgerichtete Scans in `runtime/pros` und `build/runtime-projection` auf `pros-mcp-(docx-local|microsoft-graph|office-files|powerpoint-local)` -> keine Treffer.
- Zielgerichtete Scans auf `\boffice-files\b` in denselben Bereichen -> keine Treffer.

## Acceptance Criteria
- [x] Legacy duplicate Microsoft Graph row entfernt.
- [x] API-Bridge `office-files` ersetzt.
- [x] Workflow-Doku auf `mcp-microsoft-graph` aktualisiert.
- [x] Skill-Doku auf neue Wrapper-Namen aktualisiert.
- [x] Verifikation der betroffenen Runtime-/Projection-Dateien ohne Resttreffer.
