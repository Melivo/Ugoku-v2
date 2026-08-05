# Progress Debug Agent — 20260706-143250

Status: completed

Ultrawork Phase 4 REFINE Steps 9-13 fuer die Quellenrouting-Policy ausgefuehrt.

## Durchgefuehrt

- QA-Evidenz geladen: `result-qa-agent-20260706-143250` meldet VERIFY_GATE PASS; planbezogen CRITICAL=0, HIGH=0, keine MEDIUM-Findings; breiter Lint-Fail ist bestehendes CRLF/Format-Fremdproblem.
- Serena/MCP-Codeanalyse genutzt: `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`, `search_for_pattern`, `get_diagnostics_for_file` fuer `runtime-builder.ts`, `runtime-builder.test.ts`, `init.ts`, `init.test.ts`, Skills, Workflows, Manifest, Hilfe und Plan.
- Step 9: planbezogene grosse/unsaubere Funktionen geprueft. `generateAgentsMd()` ist eine grosse Template-Funktion, aber planbezogen sauber und nicht weiter refaktoriert. Tatsaechliche Inkonsistenz im Installationspfad gefunden.
- Step 10/11: Integration und Side Effects geprueft. `generateAgentsMd()` wird ueber `buildRuntimeProjection()` von `initLocal()`/`initWorkspace()` installiert. Dort wurde `AGENTS.md` bisher ueberschrieben, obwohl der neue Hinweis Nutzerinhalte ausserhalb `PROS:START/PROS:END` als erhalten beschreibt.
- Step 12: Konsistenz der Quellenrouting-Formulierungen in Code, Tests, Skills, Workflows, Manifest und Hilfe geprueft. Keine Widersprueche bei HubSpot-Pflicht, QNAP-Zustimmung, Graph/Sync-Konflikt, Source-Status oder Preview/Freigabe gefunden.
- Step 13: Suche nach neuem totem Code und widersprechenden automatischen Abfrage-/Schreibanweisungen durchgefuehrt. Kein planbezogener toter Code nach Korrektur.

## Korrektur

Minimaler planbezogener Fix in `packages/pros-cli/src/init.ts`: `AGENTS.md` wird bei nicht-forcierten Init-/Installationslaeufen ueber `mergeProsAgentsMd()` installiert. Der verwaltete PROS-Block wird aktualisiert, Inhalte ausserhalb der Marker bleiben erhalten; legacy/unmarkierte Inhalte werden nicht verworfen. `force` bleibt weiterhin ein bewusstes Ueberschreiben.

Regressionstest in `packages/pros-cli/src/init.test.ts`: prueft Block-Ersetzung mit Erhalt manueller Abschnitte und Legacy-Erhalt ohne Marker.

## Verifikation

- `npm run test -- packages/pros-cli/src/runtime-builder.test.ts packages/pros-cli/src/init.test.ts`: PASS, 16/16.
- `npm run typecheck`: PASS.
- `npx biome check --formatter-enabled=false packages/pros-cli/src/init.ts packages/pros-cli/src/init.test.ts packages/pros-cli/src/runtime-builder.ts packages/pros-cli/src/runtime-builder.test.ts`: PASS.
- `git diff --check -- <planbezogene Dateien>`: PASS; nur bekannte Git-CRLF-Warnungen.

## Naechstes

REFINE_GATE: PASS. Keine weiteren planbezogenen Korrekturen erforderlich. Fremde `.agents`/`.opencode`-Aenderungen wurden nicht bearbeitet.
