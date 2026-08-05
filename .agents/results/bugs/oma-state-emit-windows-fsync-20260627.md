# OMA State Emit Windows fsync Failure

## Symptom

`oma state:emit --sid <sid> session.created ...` failed on Windows with:

```text
EPERM: operation not permitted, fsync
```

`oma state --activate <sid>` failed with the same error.

## Root Cause

The state metadata writer used `fsyncSync(fd)` on the temporary JSON file in
`atomicWriteJson`. On this Windows setup, `fsyncSync` can throw `EPERM` for the
local runtime path. The directory fsync path was already treated as best-effort,
but the file fsync was not, so `session.created` wrote `events.jsonl` and then
failed while refreshing `meta.json`.

## Fix

Treat the temporary-file `fsyncSync` as best-effort in both OMA state-marker
runtime copies:

- `.agents/hooks/core/state-marker.ts`
- `.opencode/plugins/oma/state-marker.ts`

The currently installed global CLI bundle was also patched in place at:

- `C:\Users\visimeos\node_modules\oh-my-agent\bin\cli.js`

## Verification

Passed:

```powershell
oma state:emit --sid ultrawork-20260627-testplan-fsync-check session.created '{"workflow":"ultrawork","category":"fsync-check"}'
oma state --activate ultrawork-20260627-testplan-fsync-check
```

Both commands completed without `EPERM`.

## Residual Risk

Updating/reinstalling the global `oh-my-agent` package can overwrite the patched
bundled `cli.js`. The source/runtime copies in this repo should be used to carry
the fix forward into the next generated package.
