# Backend Ergebnis – pros-mcp-setup-repair-20260707 – T5

Status: erledigt.

## Zusammenfassung
- `readTokenFromStdin` bleibt shared/rückwärtskompatibel und unterstützt optionale caller-spezifische Empty-/Interactive-Meldungen.
- `pros mcp qnap token set --stdin` erhält QNAP-spezifische Pipe/Paste/EOF-Hinweise und nennt redaktionssicher das Pros Credential Target `pros:qnap:mcp-assistant`.
- QNAP Token-Set/Status/Clear, Configure-Fehler, Doctor-Check und Bridge-Readiness kommunizieren das feste Pros Credential Target statt NAS-URL-Semantik.
- MCP-Konfig bleibt secret-free; Tests prüfen keine Token-/Bearer-/Secret-Leaks in Ausgaben.

## Dateien
- `packages/pros-cli/src/cli.ts`
- `packages/pros-cli/src/cli.test.ts`
- `packages/pros-cli/src/mcp-client-config.ts`
- `packages/pros-cli/src/mcp-client-config.test.ts`
- `packages/pros-cli/src/mcp-qnap-assistant.ts`
- `packages/pros-cli/src/mcp-qnap-assistant.test.ts`
- `.agents/results/result-backend-pros-mcp-setup-repair-20260707-t5.md`

## Tests / Checks
- ✅ `npm test -- --run packages/pros-cli/src/cli.test.ts packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/mcp-qnap-assistant.test.ts` — 58 Tests bestanden.
- ✅ `npm run typecheck --workspace @pro-select/pros-cli` — bestanden.
- ✅ `npx biome check packages/pros-cli/src/cli.ts packages/pros-cli/src/cli.test.ts packages/pros-cli/src/mcp-client-config.ts packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/mcp-qnap-assistant.ts packages/pros-cli/src/mcp-qnap-assistant.test.ts` — bestanden.
- ✅ `git diff --check -- <T5-Dateien>` — keine Whitespace-Fehler; nur Git LF/CRLF-Hinweise.

## Offene Risiken
- Keine Target-Migration implementiert, da nicht im Contract vorgesehen.
- Interaktive `--stdin` liest weiterhin bis EOF; UX erklärt EOF jetzt explizit.
- Package-weites Lint hatte out-of-scope Microsoft-OAuth-Formatdrift gemeldet; T5 scoped Biome ist grün.
