Status: done

Summary:
- README.md im Microsoft-Graph-Abschnitt minimal ergaenzt: Default-Redirect-URI ist jetzt explizit `http://localhost:53682/oauth/microsoft/callback`, optionaler Override ueber `PROS_MICROSOFT_REDIRECT_URI`.
- HubSpot-Redirectzeile unveraendert gelassen: `http://127.0.0.1:19876/oauth/callback`.

Files changed:
- README.md

Checks:
- README HubSpot-Abschnitt enthaelt nur die HubSpot-Callback-URL fuer HubSpot: ok.
- README Microsoft-Graph-Abschnitt enthaelt `http://localhost:53682/oauth/microsoft/callback`: ok.
- Kein Satz sagt, dass HubSpot den Graph-Redirect nutzt: ok.
- `oma docs verify --json` ausgefuehrt; Ausgabe enthaelt weiterhin zahlreiche bestehende, themenfremde Broken-Ref-Hinweise ausserhalb dieses README-Fixes.

Acceptance criteria:
- [x] README aktualisiert
- [x] HubSpot-Redirect unveraendert
- [x] Graph-Redirect explizit dokumentiert
- [x] Verifikation per Suche/MCP durchgefuehrt
- [x] Ergebnisartefakt angelegt
