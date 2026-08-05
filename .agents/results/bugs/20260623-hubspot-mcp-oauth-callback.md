# HubSpot MCP OAuth callback mismatch

## Symptom

- `opencode mcp list` showed the Pros-managed `hubspot` MCP server as failed with `MCP error -32000: Connection closed`.
- Running `pros-mcp-hubspot-remote` directly first failed with `Incompatible auth server: does not support dynamic client registration`.
- After passing static OAuth client information, HubSpot opened the browser authorization page but rejected the redirect URI.
- Browser message: `Die Autorisierung ist fehlgeschlagen, weil die Weiterleitungs-URL ... nicht mit der registrierten Weiterleitungs-URL der App uebereinstimmt.`

## Reproduction

```powershell
node packages/pros-cli/dist/mcp-hubspot-remote.js
```

Observed generated redirect URI before final host fix:

```text
http://localhost:19876/oauth/callback
```

The HubSpot MCP app was initially registered with `/mcp/oauth/callback` callback URLs, which do not match `mcp-remote`'s callback path.

## Root Cause

- `mcp-remote` does not support HubSpot dynamic client registration for this app and must receive static OAuth client information.
- The Pros wrapper only exported `HUBSPOT_MCP_CLIENT_ID` and `HUBSPOT_MCP_CLIENT_SECRET`; `mcp-remote` did not consume those as static OAuth client info, then attempted dynamic client registration.
- `mcp-remote` hard-codes the OAuth callback path to `/oauth/callback`.
- `mcp-remote` binds the local callback server to `127.0.0.1`, so the Pros wrapper should use `127.0.0.1` as the generated redirect host.

## Fix

- `packages/pros-cli/src/mcp-hubspot-remote.ts` now writes static OAuth client info to a temporary file and passes it to `mcp-remote` with `--static-oauth-client-info @<file>`.
- The wrapper starts `npx` through Node's `npx-cli.js` on Windows to avoid `spawn EINVAL` without using `shell: true`.
- The wrapper uses stable callback port `19876` and default host `127.0.0.1`.
- Temporary OAuth client info files are removed in a `finally` block.
- `packages/pros-cli/src/mcp-client-config.ts` now reports the requested client name in `--probe` warnings.
- `packages/pros-cli/src/cli.test.ts` now isolates `PROS_MCP_STATE_DIR` so tests do not read the user's global Pros MCP state.

## Required HubSpot App Configuration

Register this redirect URL in the HubSpot MCP app:

```text
http://127.0.0.1:19876/oauth/callback
```

The earlier `/mcp/oauth/callback` URLs are not used by `mcp-remote`.

## Verification

- `npm test -- mcp-hubspot-remote.test.ts mcp-client-config.test.ts`: passed.
- `npm test`: passed, 142 passed, 1 skipped.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- `npm run build`: passed.

## Residual Risk

- Live OAuth completion still requires HubSpot portal configuration to save and accept `http://127.0.0.1:19876/oauth/callback`.
- The installed global `pros` still uses the last released package until a new release is published and installed.
