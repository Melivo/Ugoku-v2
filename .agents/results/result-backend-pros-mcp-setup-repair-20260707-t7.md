# Backend Result — pros-mcp-setup-repair-20260707 Task 7

## Status

Erfolgreich abgeschlossen.

## Zusammenfassung

- `pros mcp configure` meldet fuer `microsoft-graph` nun eine fehlende `PROS_MICROSOFT_CLIENT_ID` klar als `needs_credential`, bevor ein MCP-Client-Eintrag geschrieben wird.
- `pros mcp status`/Doctor-Checks validieren bei Pros-managed Microsoft-Graph-Eintraegen nun zusaetzlich die Client-ID-Konfiguration ueber Environment oder akzeptierte OpenCode-Sync-Metadaten.
- Die statische MCP-Client-Config-Pruefung erkennt nun weitere verbotene sensitive/local-binding Werte wie Bearer-Strings, Access-/Refresh-Token, Auth-Codes, Session-IDs, Fallordner-Pfade und Allowlists.
- Regressionstests wurden fuer Microsoft-Graph-Client-ID-Meldungen und die No-secret/Sensitive-Config-Invariante erweitert.

## Dateien geaendert

- `packages/pros-cli/src/mcp-client-config.ts`
- `packages/pros-cli/src/mcp-client-config.test.ts`

Hinweis: Der Worktree enthielt bereits weitere Aenderungen aus anderen Tasks; diese wurden nicht bearbeitet.

## Verifikation

- `npx vitest run packages/pros-cli/src/mcp-client-config.test.ts` — bestanden (31 Tests)
- `npm run lint --workspace @pro-select/pros-cli` — bestanden
- `npm run typecheck --workspace @pro-select/pros-cli` — bestanden

## Akzeptanzkriterien

- [x] `pros mcp configure/status` bleibt fuer OpenCode und AnythingLLM idempotent bei erwarteten Pros-managed Eintraegen.
- [x] Fremde Eintraege werden weiterhin bewahrt; bestehende Tests decken Preservation/Overwrite-Schutz ab.
- [x] Fehlende Credentials/Client-ID werden pro Integration klar gemeldet: HubSpot, QNAP Token und Microsoft Graph Client-ID.
- [x] No-secret invariant in MCP client configs bleibt getestet und wurde fuer weitere sensitive/local-binding Muster verstaerkt.

## Out-of-scope / Risiken

- Keine Aenderungen an ZIP/Init, Microsoft OAuth internals, QNAP Assistant Implementation oder Docs.
- Kein Commit erstellt.
