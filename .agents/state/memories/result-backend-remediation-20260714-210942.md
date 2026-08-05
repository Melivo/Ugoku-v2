# Backend Remediation Result — 20260714-210942

## Status

**completed** — Der SHIP-HIGH-Befund zur OpenCode-JSONC-Kompatibilität ist behoben.

## Zusammenfassung

- `opencode.jsonc` wird für OpenCode mit `jsonc-parser` statt `JSON.parse()` gelesen.
- OpenCode-MCP-Einträge werden in vorhandenen JSONC-Dateien als gezielte Edits geschrieben beziehungsweise entfernt. Dadurch bleiben Kommentare und nicht verwaltete Einträge erhalten.
- Reine JSON-Dateien und der AnythingLLM-Schreibpfad verwenden weiterhin das bisherige JSON-Verhalten.
- Ein Regressionstest synchronisiert `docx-local`, `excel-local` und `powerpoint-local` in eine kommentierte globale OpenCode-JSONC-Datei und prüft Kommentare, fremden MCP-Eintrag sowie Managed State.
- Serena-Scope wurde nicht verändert.

## Geänderte Dateien

- `packages/pros-cli/src/mcp-client-config.ts`
  - JSONC-Parsing nur für `.jsonc`-Pfade
  - kommenterhaltende, pfadbezogene OpenCode-MCP-Edits
- `packages/pros-cli/src/mcp-client-config.test.ts`
  - Regressionstest für kommentierte OpenCode-JSONC und globale Office-MCP-Synchronisierung
- `packages/pros-cli/package.json`
  - direkte Runtime-Abhängigkeit `jsonc-parser@^3.3.1`
- `package-lock.json`
  - Lockfile-Eintrag für `jsonc-parser@3.3.1`

## Verifikation

| Prüfung | Ergebnis |
|---|---|
| `mise run test -- packages/pros-cli/src/mcp-client-config.test.ts` | PASS — 1 Datei, 36/36 Tests |
| `mise run lint` | PASS — 68 Dateien, keine Befunde |
| `mise run typecheck` | PASS |
| `mise run build` | PASS |
| `git diff --check` | PASS — keine Whitespace-Fehler; nur bestehende Windows-LF/CRLF-Hinweise |
| `mise run audit` | PASS — 0 Schwachstellen |

## Acceptance Criteria

- [x] Gültige `//`-Kommentare in `opencode.jsonc` verursachen keinen Parse-Fehler mehr.
- [x] Globale Office-MCP-Synchronisierung für DOCX, Excel und PowerPoint ist erfolgreich.
- [x] Vorhandene Kommentare bleiben erhalten.
- [x] Fremde Top-Level- und MCP-Einträge bleiben erhalten.
- [x] Managed State enthält die drei Office-MCP-Schlüssel.
- [x] AnythingLLM-Verhalten bleibt unverändert und bestehende Tests sind grün.
- [x] Serena-Scope bleibt unverändert.
- [x] Fokus-Tests, Lint, Typecheck, Build, Audit und Diff-Check sind grün.

## Hinweise

- Der Workspace enthielt bereits Änderungen aus der laufenden Session `20260714-210942`; diese Remediation hat keine fremden Änderungen zurückgesetzt oder überschrieben.
- Serena MCP war während der Ausführung wiederholt nicht erreichbar. Memory-Schreibvorgänge wurden deshalb gemäß Repository-Fallback über die lokale Serena CLI in denselben Memory Store ausgeführt.
