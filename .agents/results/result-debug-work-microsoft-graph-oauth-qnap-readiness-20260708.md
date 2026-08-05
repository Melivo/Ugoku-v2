# Debug Result: Microsoft Graph OAuth `localhost refused`

## Status

Completed (analysis/documentation only; no code changes).

## Summary

Root cause: the current Microsoft Graph OAuth user flow prepares an authorization URL with a localhost redirect (`http://localhost:53682/oauth/microsoft/callback`) but does not expose a normal supported CLI path that listens on that callback URL or otherwise completes the authorization-code exchange for end users.

Evidence:

- `packages/pros-cli/src/microsoft-oauth.ts`
  - `DEFAULT_MICROSOFT_REDIRECT_URI` is `http://localhost:53682/oauth/microsoft/callback`.
  - `createMicrosoftOAuthStart()` generates PKCE verifier/challenge, state, session id, writes a short-lived session, and returns an authorization URL.
  - `completeMicrosoftOAuth()` already implements the token exchange and OS credential-store write, but it is only an exported primitive, not reachable through a documented normal CLI command.
  - `consumeMicrosoftOAuthSession()` validates state/session expiry and deletes consumed sessions.
- `packages/pros-cli/src/cli.ts`
  - CLI help and `runCommand()` expose `pros integrations auth microsoft-graph start` and `pros integrations graph status`.
  - No visible `complete`, `callback`, or localhost listener command is wired for `integrations auth microsoft-graph`.
- `packages/pros-cli/src/integrations.ts`
  - Re-exports `completeMicrosoftOAuth()` and `consumeMicrosoftOAuthSession()`, confirming the building blocks exist for reuse.
- Existing tests confirm the gap:
  - `microsoft-oauth.test.ts` validates default redirect URI, token refresh error classification, and redaction.
  - `integrations.test.ts` covers `completeMicrosoftOAuth()` as a lower-level primitive.
  - `cli.test.ts` covers `integrations auth microsoft-graph start`, but does not cover an end-user completion command/listener.
- Docs currently document `start` as URL/session preparation and `graph status`, but do not provide an official user-facing completion path that prevents the browser from landing on an unserved localhost callback.

Observed verification:

- Serena CLI indexing was run for the requested files with `serena project index-file ... --verbose`.
- Targeted tests passed: `npm test -- packages/pros-cli/src/microsoft-oauth.test.ts packages/pros-cli/src/cli.test.ts` => 2 test files, 32 tests passed.
- Local port probe during analysis found no listener on `127.0.0.1:53682` in the current session.

## Nutzerfolgen

- After a user runs `pros integrations auth microsoft-graph start` and opens the returned Microsoft authorization URL, Microsoft redirects the browser to `http://localhost:53682/oauth/microsoft/callback?...`.
- Because no Pros callback server/listener is started by the visible flow, the browser can show `localhost refused` / cannot connect after successful Microsoft consent.
- The error is misleading: it looks like a network/browser/local-machine failure, while the real issue is an incomplete product UX path.
- Tokens are not stored, so `pros integrations graph status` remains `needs-auth` / `needs-reauth` even after the user completed Microsoft consent in the browser.
- Users may incorrectly troubleshoot MCP client configuration, QNAP setup, firewall, or Azure app configuration, although this specific failure is caused by the missing completion path. Azure errors such as `AADSTS700016` remain a separate app/tenant/client-id issue.

## Betroffene Symbole und CLI-Pfade

- `packages/pros-cli/src/microsoft-oauth.ts`
  - `DEFAULT_MICROSOFT_REDIRECT_URI`
  - `createMicrosoftOAuthStart()`
  - `buildMicrosoftAuthorizationUrl()`
  - `consumeMicrosoftOAuthSession()`
  - `completeMicrosoftOAuth()`
  - `refreshMicrosoftToken()`
- `packages/pros-cli/src/integrations.ts`
  - Re-exports `completeMicrosoftOAuth`, `consumeMicrosoftOAuthSession`, `createMicrosoftOAuthStart`.
- `packages/pros-cli/src/cli.ts`
  - `HELP_TEXT`
  - `parseArgs()` for `integrations auth microsoft-graph start`
  - `runCommand()` branch for `integrations auth microsoft-graph start`
  - Missing branch for a supported completion/listener path.
- User-facing commands:
  - Existing: `pros integrations auth microsoft-graph start`
  - Existing: `pros integrations graph status [profileId]`
  - Missing/required: supported callback listener and/or explicit completion command that calls `completeMicrosoftOAuth()`.

## Empfohlene Fix-Anforderungen

1. Choose and document the official completion UX:
   - Preferred: listener-first command, e.g. `pros integrations auth microsoft-graph login` or enhanced `start --listen`, that opens/prints the URL, binds only to loopback, validates callback path/state/session, calls `completeMicrosoftOAuth()`, and returns a redaction-safe success/failure page plus CLI output.
   - Acceptable fallback: explicit complete command, e.g. `pros integrations auth microsoft-graph complete --session <id> --state <state> --code <code>`, with clear browser-copy instructions; this should be a documented fallback, not the only normal path if the desired UX is browser-first.
2. Reuse `completeMicrosoftOAuth()` for token exchange and credential-store persistence. Do not duplicate OAuth token logic.
3. Preserve PKCE/session safety:
   - State must match.
   - Session id must pass the existing pattern.
   - Expired sessions must fail closed and be removed.
   - Callback must reject missing/empty `code`, `error`, and mismatched state with actionable redacted messages.
4. Bind local listener safely:
   - Listen only on loopback (`127.0.0.1` and/or `localhost` as intentionally chosen).
   - Use the configured redirect URI port/path and detect occupied port before telling users to continue.
   - Provide a clear fallback if bind/browser launch fails.
5. Update CLI help and docs:
   - `start` must no longer imply OAuth is complete after URL generation.
   - Help/docs must show the exact next step and how to verify with `pros integrations graph status`.
6. Maintain redaction guarantees:
   - Never print authorization code, access token, refresh token, bearer header, client secret, or raw token endpoint payload.
   - Continue storing Microsoft credentials only in the OS Credential Store target.

## Empfohlene Fix-Akzeptanzkriterien

- [ ] A normal user can complete Microsoft Graph OAuth through a supported `pros` command without manual Node snippets.
- [ ] Browser redirect no longer lands on an unexplained unserved localhost page in the happy path.
- [ ] The implementation calls `completeMicrosoftOAuth()` for token exchange and credential storage.
- [ ] Successful completion stores tokens only in the OS Credential Store and prints only redacted metadata such as credential target, expiry, and scopes.
- [ ] State mismatch, expired session, missing code, OAuth `error`, occupied port, missing client id, invalid redirect URI, and `AADSTS700016` produce actionable redaction-safe failures.
- [ ] `pros integrations graph status` reports a useful post-auth status after successful completion.
- [ ] CLI help and `docs/MCP-CREDENTIALS.md` / `docs/CLI-MCP-COMMANDS.md` describe the supported completion path and fallback.
- [ ] Regression tests cover listener/complete success, state mismatch, session expiry, missing code, port-bind failure/fallback, and secret redaction.

## Risiken / Hinweise fuer Folge-Agenten

- Azure App Registration must include the exact redirect URI used by the CLI. A mismatch can produce a separate Azure redirect/configuration error.
- `localhost` may resolve to IPv6 `::1` on some systems; listener binding and docs should avoid host mismatch between registered redirect URI and bound address.
- Port `53682` can be occupied; the fix must fail with clear instructions or support a configured redirect override that remains consistent with Azure registration.
- Automatic browser opening is convenient but can fail in headless/remote shells; keep a copy/paste URL fallback.
- Do not expand scope into QNAP behavior in this task; QNAP readiness belongs to downstream workflow tasks.

## Files Changed

- Added analysis artifact: `.agents/results/result-debug-work-microsoft-graph-oauth-qnap-readiness-20260708.md`
- No source code or documentation files were modified.

## Acceptance Criteria Checklist

- [x] Root cause documented as a product/UX bug.
- [x] Cause is clear: `start` creates localhost redirect but no visible normal listener/completion command completes the flow.
- [x] Existing OAuth primitives are identified for reuse.
- [x] Concrete affected symbols and CLI paths listed.
- [x] Actionable fix acceptance criteria and risks documented.
- [x] No secrets printed.
