# Result Backend — work-20260704-pros-desktop-assets

Status: DONE

## Zusammenfassung
- P0 fuer Pros Desktop Assets umgesetzt.
- Drei Desktop-Assets unter `runtime/pros/desktop-assets/` abgelegt; Zielnamen exakt erhalten.
- `buildRuntimeProjection` kopiert `runtime/pros/desktop-assets` deterministisch via `copyRequiredDir` nach `<outputDir>/desktop-assets`.
- `packages/pros-cli/src/init.ts` enthaelt nun testbare Desktop-Installationslogik (`resolveDesktopDir`, `installDesktopAssets`) mit Datei-only-Kopie, Idempotenz, Force-Overwrite und Konfliktwarnungen.
- `initLocal` nutzt `stagingDir/desktop-assets`; `initWorkspace` nutzt `extractDir/desktop-assets`; Desktop-Ziele werden nicht an `hideOnWindows` uebergeben.

## Geaenderte Dateien
- `runtime/pros/desktop-assets/API Nutzung von LLMs.png`
- `runtime/pros/desktop-assets/Model Selection Guide - Mistral Docs.url`
- `runtime/pros/desktop-assets/OpenCode TUI.lnk`
- `packages/pros-cli/src/runtime-builder.ts`
- `packages/pros-cli/src/init.ts`

## Verifikation
- PASS: `npm run typecheck --workspace @pro-select/pros-cli`
- PASS: `npm run lint --workspace @pro-select/pros-cli`
- PASS: `npm test --workspace @pro-select/pros-cli -- runtime-builder`
- PASS: `npm test --workspace @pro-select/pros-cli -- init`
- PASS: `git diff --check -- packages/pros-cli/src/init.ts packages/pros-cli/src/runtime-builder.ts` (nur CRLF-Hinweise, keine Whitespace-Fehler)
- PASS: Desktop-Asset-Dateien sind nicht leer und enthalten nach Scan keine nutzerspezifischen Profilpfade (`visimeos`, `C:\\Users`, `AppData`).

## Hinweise / offene Punkte
- Tests fuer die neue Desktop-Installationslogik sind als P1 bei QA geplant; Export-Anpassungen dafuer sind vorhanden.
- Der zuerst kopierte `OpenCode TUI.lnk` enthielt eine user-spezifische WindowsApps-Zielpfadangabe; der Shortcut wurde mit gleichem Dateinamen auf eine generische `cmd.exe /k opencode`-Variante umgestellt, damit keine Profilpfade ausgeliefert werden.
- Repo enthaelt viele vorbestehende Aenderungen anderer Agenten; diese wurden nicht revertiert.

## Acceptance Criteria Checklist
- [x] Drei Desktop-Dateien unter `runtime/pros/desktop-assets/` vorhanden.
- [x] Zielnamen exakt erhalten.
- [x] `buildRuntimeProjection` kopiert `desktop-assets` via `copyRequiredDir`.
- [x] Fehlende Projektionsquelle wuerde deterministisch fehlschlagen.
- [x] `resolveDesktopDir`/injizierbare Installationslogik vorhanden.
- [x] Nur Dateien aus dem Asset-Ordner werden kopiert.
- [x] Identische Zieldateien sind idempotent.
- [x] Abweichende Zieldateien werden ohne Force nicht still ueberschrieben; Warnung/Rueckgabe vorhanden.
- [x] Force-Overwrite wird unterstuetzt.
- [x] Desktop-Ziele rufen nicht `hideOnWindows` auf.
- [x] Local- und Remote-Init-Phase eingebunden.
- [x] Init-Erfolgsmeldungen nennen Desktop-Asset-Ergebnis knapp.
