Status: done
Summary: README.md im Microsoft-Graph-Abschnitt minimal ergaenzt: Default-Redirect-URI ist jetzt explizit `http://localhost:53682/oauth/microsoft/callback`, optionaler Override ueber `PROS_MICROSOFT_REDIRECT_URI`. HubSpot-Redirectzeile blieb unveraendert bei `http://127.0.0.1:19876/oauth/callback`.
Files changed: README.md
Checks: README HubSpot-Abschnitt enthaelt nur die HubSpot-Callback-URL fuer HubSpot; README Microsoft-Graph-Abschnitt enthaelt `http://localhost:53682/oauth/microsoft/callback`; kein Satz sagt, dass HubSpot den Graph-Redirect nutzt; `oma docs verify --json` lief und zeigte weiterhin zahlreiche themenfremde bestehende Broken-Ref-Hinweise ausserhalb dieses README-Fixes.
