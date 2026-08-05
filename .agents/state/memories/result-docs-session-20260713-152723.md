## Status: completed

### Summary
Repaired HubSpot credential documentation/runtime workflow guidance. The workflow now provides a complete masked PowerShell pipeline, forbids inventing a second prompt, and README no longer uses the rendering-sensitive NetworkCredential conversion.

### Files changed
- README.md
- docs/CLI-MCP-COMMANDS.md
- docs/MCP-CREDENTIALS.md
- runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md
- runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/auth-and-credentials.md
- runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/debugging.md

### Verification
- Focused static searches passed for scoped HubSpot guidance.
- `oma docs verify --json` reports pre-existing repository drift: brokenCount=344 (file=339, script=5); no new scoped issue.
- No secrets introduced.

### Acceptance criteria
- [x] No false second-prompt claim.
- [x] Complete masked PowerShell pipeline.
- [x] Direct TTY semantics coordinated with backend target behavior.
- [x] README escaped-bracket risk removed.
