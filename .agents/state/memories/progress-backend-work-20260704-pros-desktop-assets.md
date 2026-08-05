# Fortschritt Backend — work-20260704-pros-desktop-assets

Status: implementiert, Verifikation laeuft/abgeschlossen

- Stack erkannt: TypeScript/Node.js CLI-Paket `@pro-select/pros-cli`, ESM, Vitest, TypeScript Build, Biome.
- Drei Desktop-Assets aus `C:\Users\visimeos\Desktop` gezielt nach `runtime/pros/desktop-assets/` kopiert; Zielnamen exakt erhalten.
- `buildRuntimeProjection` kopiert jetzt `runtime/pros/desktop-assets` via `copyRequiredDir` nach `<outputDir>/desktop-assets`.
- `init.ts` erweitert um exportierte, testbare Desktop-Logik: `resolveDesktopDir`, `installDesktopAssets`, Force-/Konflikt-/Idempotenzverhalten, Datei-only-Kopie und Warnungsrueckgabe.
- `initLocal` nutzt `stagingDir/desktop-assets`; `initWorkspace` nutzt `extractDir/desktop-assets`; Desktop-Ziele werden nicht an `hideOnWindows` uebergeben.
- Smokes bisher erfolgreich: `npm run typecheck --workspace @pro-select/pros-cli`, `npm run lint --workspace @pro-select/pros-cli`, `npm test --workspace @pro-select/pros-cli -- runtime-builder`.
- Hinweis: Repo enthaelt viele vorbestehende Aenderungen anderer Agenten; nicht revertiert.
