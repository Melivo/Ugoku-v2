# Backend Ergebnis – pros-mcp-setup-repair-20260707 – T5

## Status

Erledigt.

## Zusammenfassung

- `readTokenFromStdin` bleibt shared/rückwärtskompatibel, akzeptiert jetzt aber optionale caller-spezifische Empty-/Interactive-Meldungen.
- `pros mcp qnap token set --stdin` nutzt jetzt QNAP-spezifische Hinweise zu Pipe/Paste/EOF und nennt redaktionssicher das Pros Credential Target `pros:qnap:mcp-assistant`.
- QNAP Token-Set/Status/Clear, Configure-Fehler, Doctor-Check und Bridge-Readiness kommunizieren das feste Pros Credential Target statt NAS-URL-Semantik.
- MCP-Client-Konfiguration bleibt secret-free; neue Tests prüfen, dass keine Tokens/Bearer/Secretwerte in Status-/Readiness-Meldungen auftauchen.

## Dateien geändert

- `packages/pros-cli/src/cli.ts`
- `packages/pros-cli/src/cli.test.ts`
- `packages/pros-cli/src/mcp-client-config.ts`
- `packages/pros-cli/src/mcp-client-config.test.ts`
- `packages/pros-cli/src/mcp-qnap-assistant.ts`
- `packages/pros-cli/src/mcp-qnap-assistant.test.ts`

## Verifikation

- ✅ `npm test -- --run packages/pros-cli/src/cli.test.ts packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/mcp-qnap-assistant.test.ts` — 3 Dateien, 58 Tests bestanden.
- ✅ `npm run typecheck --workspace @pro-select/pros-cli` — bestanden.
- ✅ `npx biome check packages/pros-cli/src/cli.ts packages/pros-cli/src/cli.test.ts packages/pros-cli/src/mcp-client-config.ts packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/mcp-qnap-assistant.ts packages/pros-cli/src/mcp-qnap-assistant.test.ts` — bestanden.
- ✅ `git diff --check -- <geänderte T5-Dateien>` — keine Whitespace-Fehler; Git meldet nur Windows-LF/CRLF-Hinweise.

Hinweis: Ein früherer Package-weite `npm run lint --workspace @pro-select/pros-cli`-Lauf meldete zusätzlich out-of-scope Formatdrift in Microsoft-OAuth-Dateien. Diese Dateien wurden für T5 nicht geändert.

## Akzeptanzkriterien

- [x] `pros mcp qnap token set --stdin` hat eindeutige Bedienung und Fehlermeldung, inklusive leerem stdin.
- [x] Status prüft und kommuniziert das dokumentierte Credential Target `pros:qnap:mcp-assistant` redaktionssicher.
- [x] Keine Anleitung oder CLI-Ausgabe widerspricht dem Target; keine Secrets in MCP-Konfig.

## Offene Risiken / Hinweise

- Keine Target-Migration implementiert, da kein konkreter Bedarf im Contract vorgesehen ist.
- Interaktive `--stdin`-Eingabe liest weiterhin bis EOF; der Fix macht das Verhalten explizit statt es in einen anderen Secret-Eingabemodus umzubauen.
- Working Tree enthält bereits weitere Änderungen/Artefakte außerhalb T5 (u. a. Microsoft/ZIP/Planartefakte); sie wurden nicht bearbeitet.
