## Status: completed

### Summary

Fixed the HubSpot credential setup hang at its root: `readTokenFromStdin()` now detects the actual interactive `process.stdin` TTY and returns after the first complete non-empty line, while redirected/custom async input continues reading until EOF. Added safe, TTY-only Enter guidance for HubSpot and aligned the existing QNAP and Microsoft OAuth interactive messages with the new behavior.

### Diagnosis

The baseline helper used `for await ... of input` for every stdin mode. Pressing Enter on a TTY emits a chunk containing a newline but does not close `process.stdin`, so the HubSpot credential-store call and `Status: ready` output were never reached.

### Files changed

- `packages/pros-cli/src/cli.ts`
  - TTY-only first-complete-line return.
  - Piped/redirected EOF path unchanged.
  - Secret-free interactive prompts now instruct one Enter.
- `packages/pros-cli/src/cli.test.ts`
  - HubSpot TTY regression test with mocked stdin and credential store.
  - Piped multi-chunk/EOF compatibility regression test.

### Verification

- `npm test -- --run src/cli.test.ts` — passed, 35/35 tests.
- `npm run typecheck` — passed.
- `npm run lint` — passed.
- `git diff --check -- packages/pros-cli/src/cli.ts packages/pros-cli/src/cli.test.ts` — passed (only expected Windows line-ending warnings).
- Serena diagnostics for both touched files/regions — no diagnostics.
- Similar-pattern scan — no other stdin consumption loop found; all four `readTokenFromStdin()` caller paths reviewed.

### Acceptance criteria

- [x] Direct actual-stdin TTY mode completes after one non-empty line and Enter, without waiting for EOF.
- [x] HubSpot command reaches a clear `Status: ready` result after the line is read.
- [x] Redirected/piped multi-chunk input remains pending until EOF and preserves concatenated input behavior.
- [x] Regression tests use fake values only; credential storage is mocked and stdout/stderr do not contain the fake secret.
- [x] Existing `interactiveMessage` output remains TTY-only and secret-free.
- [x] README, docs, and runtime workflow files were not edited by this debug task.

### Out-of-scope findings

None. Concurrent pre-existing worktree changes outside the two CLI files were left untouched.
