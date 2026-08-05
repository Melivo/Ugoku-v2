# Debug Progress

- Session: `session-20260713-152723`
- Status: completed
- Root cause: baseline `readTokenFromStdin()` consumed actual TTY stdin until EOF; Enter emitted data but did not end the async iterator.
- Fix: actual `process.stdin` with `isTTY` returns after the first complete non-empty line; redirected/custom input remains EOF-based. TTY prompts for HubSpot, QNAP, and Microsoft OAuth now accurately say to press Enter once.
- Regression coverage: HubSpot TTY command completes after one fake line without a second read, emits a clear ready result, and does not print the fake secret; piped multi-chunk input remains pending until controlled EOF.
- Similar-pattern scan: no second stdin read-until-EOF loop found in package sources; all helper callers reviewed.
- Verification: `npm test -- --run src/cli.test.ts` (35 passed), `npm run typecheck` (passed), `npm run lint` (passed), `git diff --check` (passed; Windows line-ending warnings only).
- Files modified: `packages/pros-cli/src/cli.ts`, `packages/pros-cli/src/cli.test.ts`.
