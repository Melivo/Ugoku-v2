# PM Review: Docling als globalen Tool-Skill (Plan 022)

**Session**: 20260704-docling-tool-skill
**Status**: completed
**Reviewed plans**: `.agents/results/plan-20260704-docling-tool-skill.json`, `docs/plans/work/022-docling-global-tool-skill.md`

## Summary

Der Plan ist technisch fundiert und mit der tatsaechlichen Codebasis konsistent. Code-Verifikation bestaetigt alle betroffenen Bereiche. Die wichtigste Erkenntnis: Die Docling-Quelldateien bleiben an `runtime/pros/.agents/skills/docling/` als **gemeinsame Quelle** fuer `pros tools`, weil `resolveSourceSkillsDir()` (tool-skills.ts:79-95) in der Entwicklung auf dasselbe Verzeichnis zeigt. Es findet also keine Dateiverschiebung statt, sondern eine Umklassifizierung in zwei Konstanten.

## Code-Verifikation gegen Planannahmen

| Annahme | Fund in Code | Status |
|---|---|---|
| `docling` in `LOCAL_RUNTIME_SKILLS` | runtime-builder.ts:28 | bestaetigt - muss entfernt werden |
| `docling` fehlt in `GLOBAL_TOOL_SKILLS` | tool-skill-list.ts:1-9 | bestaetigt - muss hinzugefuegt werden |
| Quelle fuer Tool-Skills = runtime/pros/.agents/skills | tool-skills.ts:84-94 | bestaetigt - kein Move noetig |
| Test erwartet docling lokal | runtime-builder.test.ts:46,205-213 | bestaetigt - muss umgedreht werden |
| tool-skills.test nutzt importierte Konstante | tool-skills.test.ts:37,82 | bestaetigt - self-updating nach Task 2 |
| Manifest beschreibt docling als lokal | pros-runtime-manifest.md:23 | bestaetigt - muss korrigiert werden |
| Konfliktschutz fuer fremde Ordner existiert | tool-skills.ts:227-246 | bestaetigt - gilt automatisch fuer docling |

## API-Contract-Status

**Nicht erforderlich.** Richtig so. `tool-skill-list.ts` ist eine interne TS-Konstante, keine serviceuebergreifende Schnittstelle. Es entsteht keine neue Frontend-/Backend-/Service-API. Kein Contract-Artefakt noetig.

## Files Changed (geplant, keine Implementierung)

- `packages/pros-cli/src/runtime-builder.ts` - `docling` aus `LOCAL_RUNTIME_SKILLS` entfernen
- `packages/pros-cli/src/tool-skill-list.ts` - `docling` zu `GLOBAL_TOOL_SKILLS` hinzufuegen
- `packages/pros-cli/src/runtime-builder.test.ts` - docling von Present- auf Absent-Assertion umstellen
- `packages/pros-cli/src/tool-skills.test.ts` - ggf. explizite docling-Erwartung (self-updating via Import)
- `runtime/pros/pros-runtime-manifest.md` - Zeile 23 umformulieren
- `runtime/pros/.agents/skills/docling` - bleibt als Tool-Skill-Quelle unveraendert

## Acceptance Criteria Checklist

- [ ] `docling` nicht in `LOCAL_RUNTIME_SKILLS`
- [ ] `docling` in `GLOBAL_TOOL_SKILLS`
- [ ] `buildRuntimeProjection` kopiert docling nicht in Runtime-Output
- [ ] `runtime-builder.test.ts` erwartet docling NICHT in Skills, stattdessen in Absent-Liste
- [ ] `tool-skills.test.ts` deckt docling-Installation ab (via importierter Konstante)
- [ ] Konfliktschutz fuer fremdverwaltete docling-Ordner bleibt getestet
- [ ] Manifest beschreibt docling als globalen Tool-Skill
- [ ] `npm --workspace @pro-select/pros-cli test` gruen
- [ ] `npm --workspace @pro-select/pros-cli run lint` gruen
- [ ] `npm --workspace @pro-select/pros-cli run typecheck` gruen
- [ ] `node scripts/validate-runtime-files.js` gruen

## PM Gap-Hinweis (P2, nicht blockierend)

Bestehende Konfliktschutz-Logik (tool-skills.ts:235) behandelt den Migrationsfall sicher: Ein Endnutzer, der docling bereits via `pros init` in seinem Fallordner hat, wuerde beim `pros tools` den Status `foreign-conflict` erhalten und der Ordner wird nicht ueberschrieben. Kein Datenverlust, aber ggf. UX-Hinweis fuer Support wert. Da `pros` pre-release ist, wahrscheinlich kein echter Nutzer betroffen.
