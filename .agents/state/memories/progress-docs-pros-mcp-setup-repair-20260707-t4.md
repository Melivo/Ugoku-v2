Status: started
Task: P0 Task 4 - Microsoft-Graph Setup-Dokumentation synchronisieren
Scope: README, CLI/MCP docs, runtime help, plan tracker entries that mention Microsoft Graph setup
Known contract: redirect default `http://localhost:53682/oauth/microsoft/callback`; client ID from `PROS_MICROSOFT_CLIENT_ID`; optional `PROS_MICROSOFT_TENANT_ID`, `PROS_MICROSOFT_REDIRECT_URI`; AADSTS700016 is Azure app/tenant/client-ID config, not MCP client config
Next: inspect docs for legacy redirects (`19876`, `/auth/microsoft/callback`) and Graph setup wording before patching