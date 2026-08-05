Status: done

Summary:
- Microsoft Graph setup docs aligned to one contract: redirect URI `http://localhost:53682/oauth/microsoft/callback`.
- Client-ID flow is now documented via Azure App Registration and `PROS_MICROSOFT_CLIENT_ID`.
- `AADSTS700016` is documented as an Azure app/tenant/client-ID issue, not a MCP client-config issue.

Files changed:
- README.md
- docs/CLI-MCP-COMMANDS.md
- docs/MCP-CREDENTIALS.md
- docs/pros-hilfe-src/endnutzerhandbuch.md
- runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md

Checks:
- `oma docs verify --json` => scannedDocs 997, totalRefs 5274, skippedCount 203, brokenCount 325
- Targeted greps confirmed the old Microsoft Graph redirect values were removed from the in-scope docs

Acceptance criteria:
- [x] README, CLI/MCP-Doku und Runtime-Anleitung nennen dieselbe Redirect-URI.
- [x] Client-ID-Setup-Pfad ist einheitlich dokumentiert.
- [x] AADSTS700016-Troubleshooting ist redaktionssicher beschrieben.
- [x] Keine Secrets oder echten IDs ergaenzt.
