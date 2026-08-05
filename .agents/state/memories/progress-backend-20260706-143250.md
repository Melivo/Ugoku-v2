# Progress Backend — 20260706-143250

## Status
Implementierung umgesetzt; lokale Testausführung blockiert, weil `node_modules/.bin/vitest.cmd` fehlt.

## Fortschritt
- Stack erkannt: TypeScript/Node.js-Monorepo mit Vitest/Biome.
- Serena-Codeanalyse genutzt: `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`, `search_for_pattern`.
- `generateAgentsMd()` in `packages/pros-cli/src/runtime-builder.ts` um zentrale Quellenrouting-Policy erweitert.
- `runtime-builder.test.ts` um stabile Assertions für HubSpot, QNAP/NAS, Microsoft Graph/SharePoint/OneDrive-Konflikt, Source-Status, Preview-Freigabe und PROS-Block-Erhalt ergänzt.
- Acht Primärskills minimal auf zentrale Fallordner-`AGENTS.md`-Policy ausgerichtet.
- Acht Workflows um Quellenprüfung vor Synthese/Ergebnisdarstellung ergänzt.
- MCP-Setup-Skills per Scan geprüft; keine fachliche Änderung vorgenommen.
- Runtime-Manifest und Endnutzerhilfe in einfacher Sprache aktualisiert.
- P3-Folgepunkt Windows-Syncroot-Detector im Plantracker dokumentiert.

## Tests/Checks
- Versuch: `npm run test -- packages/pros-cli/src/runtime-builder.test.ts`.
- Ergebnis: blockiert durch fehlendes `vitest`-Binary.
- Zusatzprüfung: `node_modules` existiert, aber `vitest.cmd`, `tsc.cmd`, `biome.cmd` fehlen.

## Offene Blocker
- Lokale Dependencies/Binaries fehlen; keine Installation durchgeführt.
- Arbeitsbaum enthält viele fremde Änderungen in root `.agents/`/`.opencode/`; nicht angefasst.