# result-docs-pros-mcp-setup-repair-20260707-t8-remediation

## Status
Erledigt.

## Zusammenfassung
- README.md: HubSpot-Redirect korrigiert auf `http://127.0.0.1:19876/oauth/callback`.
- Microsoft-Graph-Abschnitt unveraendert gelassen; dort bleibt `http://localhost:53682/oauth/microsoft/callback` nur im Graph-Kontext referenziert.

## Geaenderte Dateien
- `README.md`
- `.agents/results/result-docs-pros-mcp-setup-repair-20260707-t8-remediation.md`

## Verifikation
- [x] HubSpot-Abschnitt nennt `127.0.0.1:19876/oauth/callback`.
- [x] Microsoft-Graph-Abschnitt nennt `localhost:53682/oauth/microsoft/callback`.
- [x] Keine Aussage im HubSpot-Abschnitt legt nahe, dass HubSpot den Microsoft-Graph-Redirect nutzt.
