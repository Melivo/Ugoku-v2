# PM Fortschritt — work-20260704-pros-desktop-assets

Status: Ready-for-work (Plan erstellt)
Datum: 2026-07-04

## Artefakte
- Umsetzungsnaher Plan: `.agents/results/plan-work-20260704-pros-desktop-assets.json`
- Freigegebener Basisplan: `.agents/results/plan-20260704-pros-desktop-assets.json`
- Human Tracker: `docs/plans/work/023-pros-desktop-assets.md`

## API-Contract
- `apiContractRequired = false`. Kein Frontend-/Backend-/Servicevertrag. Keine `.agents/results/api-contracts/`-Datei erzeugt.

## Technische Kernaussagen (Codeanalyse)
- `buildRuntimeProjection` (runtime-builder.ts:272-421): Desktop-Assets via `copyRequiredDir` nach pros-Hilfe-Pattern projizieren.
- `copyRequiredDir` (154-160): wirft deterministisch bei fehlendem Ordner.
- `RUNTIME_INSTALL_ENTRIES` (init.ts:28-35): kopiert ins Workspace + versteckt. Desktop-Assets duerfen NICHT dort rein.
- `initLocal` (97-182) und `initWorkspace` (328-489): brauchen je eine separate Desktop-Phase OHNE `hideOnWindows`.
- `hideOnWindows` (201-209): attrib +h — niemals fuer Desktop-Ziele aufrufen.
- `manifest.ts` scanDirectory (42-68): nimmt desktop-assets automatisch auf, KEINE Aenderung an manifest.ts noetig.
- Testpattern: runtime-builder.test.ts (mkdtemp + listFiles + access); init.test.ts testet initLocal/initWorkspace nicht direkt -> Desktop-Logik muss als injizierbare Funktion extrahiert werden.

## Tasks (Wellen)
- Wave 1: T1 (Assets ablegen) — backend P0
- Wave 2: T2 (buildRuntimeProjection erweitern) — backend P0
- Wave 3: T3 (resolveDesktopDir + installDesktopAssets extrahieren) — backend P0
- Wave 4: T4 (initLocal + initWorkspace Desktop-Phase) — backend P0
- Wave 5 parallel: T5 (Tests) qa P1, T6 (Doku) backend P1, T7 (Release-Check) qa P1

## Akzeptanz-Highlights
- Drei Dateien in runtime/pros/desktop-assets/ mit exakten Namen (inkl. Leerzeichen/Umlaute).
- Desktop-Dateien werden sichtbar (kein hideOnWindows), Konflikt ohne force = Skip.
- Desktop-Pfad-Aufloesung injizierbar -> Tests mutieren nie den echten Desktop.
- manifest.ts bleibt unveraendert; Root-.agents/ bleibt unveraendert.

## Offene Risiken
- Windows-Desktop-Pfad variiert (OneDrive, Locale) — medium.
- .lnk evtl. von Release-Filtern ausgeschlossen — medium, durch T7 abgefangen.
- Graceful-Degradation verschluckt Fehler — low, durch dokumentierte Rueckgabe + Tests.

## Naechster Schritt
- /work kann starten: T1 ausfuehren, dann wellenweise vorgehen.
