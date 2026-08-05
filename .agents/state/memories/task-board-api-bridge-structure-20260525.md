# Task Board: API Bridge Config/Install Structure

Session: ultrawork-api-bridge-structure-20260525
Scope: first-party API bridge config/install model for integrations without validated MCP servers. No OAuth token exchange.

## P0
- [x] Define provider registry and bridge capability/policy model in pros CLI.
- [x] Implement global non-secret profiles file under `%LOCALAPPDATA%/pros/integrations/profiles.json` with validation and safe defaults.
- [x] Add OS credential-store abstraction/contract for future bridge secrets without persisting tokens in files.
- [x] Add case-local `.pros/integrations.json` non-secret allowlist reader/validator.
- [x] Wire `pros integrations status` to merge Pros Runtime Manifest, global profiles, credential availability, and case allowlists.
- [x] Add tests for no-secret persistence, validation errors, profile/case merge behavior, and status output.

## P1
- [x] Add minimal `pros integrations profile` commands for list/show/set non-secret settings. (`profile list` implemented; write/set intentionally deferred.)
- [x] Add install/preflight command that reports manual actions without installing third-party MCP servers. (`preflight` implemented.)
- [ ] Update docs for admins and end users.

## Deferred
- [ ] OAuth token exchange and refresh handling.
- [ ] Provider data operations beyond readiness/status checks.
- [ ] QNAP remote access automation.
