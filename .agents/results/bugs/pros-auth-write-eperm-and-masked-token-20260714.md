# Pros Auth Write EPERM And Masked Token

## Symptom

`pros auth token set --stdin` failed on Windows with:

```text
EPERM: operation not permitted, open '%LOCALAPPDATA%\\pros\\auth.json'
```

The README also prompted for the Pros release token without PowerShell's `-MaskInput`.

## Root Cause

The CLI correctly reads the token from stdin, but `setToken()` calls `saveAuthConfig()`, which writes `%LOCALAPPDATA%\\pros\\auth.json`. The existing hidden local auth directory/file could not be overwritten. The exact Windows-level cause remains environment-specific (ACL, lock, antivirus, or stale attributes).

## Fix And Verification

- Cleared the hidden attribute from `%LOCALAPPDATA%\\pros` and `auth.json`, removed the stale file, and verified a test token can be written.
- Added `-MaskInput` to the README release-token prompt.
- Updated matching copyable guidance in the first-use test plan and prior remediation report.
- Added a Vitest regression test in `tests/release-workflow.test.ts` that requires the masked README prompt.
- Verified with `node node_modules/vitest/vitest.mjs run tests/release-workflow.test.ts`: 9 tests passed.

## Similar Patterns

The two copyable unmasked release-token prompts in `docs/plans/work/017-pros-first-use-setup-test.md` and `.agents/results/bugs/pros-windows-enduser-init-auth-store-20260704.md` were corrected. Historical discussion of unmasked input was left unchanged.
