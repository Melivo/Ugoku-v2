Session: pros-mcp-setup-repair-20260707
Task: P1 Task 8 monitoring finding remediation

Outcome:
- Fixed README.md HubSpot-MCP section to use the HubSpot redirect URL `http://127.0.0.1:19876/oauth/callback`.
- Left Microsoft Graph README section unchanged; it still uses `http://localhost:53682/oauth/microsoft/callback` only in the Graph context.
- Added a remediation note at `.agents/results/result-docs-pros-mcp-setup-repair-20260707-t8-remediation.md`.

Verification:
- README HubSpot section now contains `http://127.0.0.1:19876/oauth/callback`.
- README Microsoft Graph section still contains `http://localhost:53682/oauth/microsoft/callback`.
- No HubSpot wording implies the Microsoft Graph redirect is the HubSpot redirect.

No secrets touched. No commit.