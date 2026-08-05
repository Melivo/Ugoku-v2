# OMA agent:spawn false crashed status on successful short runs

## Symptom

On Windows, `oma agent:spawn` printed `Exited with code 0`, but `oma agent:status` reported the same agent as `crashed`.

Reproduction command:

```powershell
oma agent:spawn backend-engineer "Mini debug reproduction only. Reply exactly HELLO_DEBUG_REPRO and do not inspect files." debug-opencode-spawn-20260627 -w .
oma agent:status debug-opencode-spawn-20260627 backend-engineer
```

Observed result before the fix:

```text
[backend-engineer] Exited with code 0
backend-engineer:crashed
```

The log path printed by `agent:spawn` was also removed after child exit.

## Root Cause

The installed OMA runtime at `C:/Users/visimeos/node_modules/oh-my-agent/bin/cli.js` wrote a temp PID and log for spawned agents, then deleted both on every child exit.

`agent:status` only checked:

1. `.serena/memories/result-{agent}.md`
2. `%TEMP%/subagent-{session}-{agent}.pid` and whether that PID was alive
3. otherwise `crashed`

A successful short-lived child with no result memory was therefore indistinguishable from a crashed child once cleanup removed the PID and log.

## Fix Applied

Patched the installed OMA bundle so child exit writes a session-specific terminal status file before cleanup:

```text
%TEMP%/subagent-{session}-{agent}.status
```

`agent:status` now checks that session-specific `.status` file before falling back to generic result memory or PID state.

This avoids using generic `.serena/memories/result-{agent}.md` for synthetic completion status, because that file is not session-specific and can make older sessions appear completed.

## Verification

Commands:

```powershell
node -c C:\Users\visimeos\node_modules\oh-my-agent\bin\cli.js
oma --version
oma agent:status debug-opencode-spawn-20260627 backend-engineer
oma agent:spawn backend-engineer "Mini regression test only. Reply exactly HELLO_FIXED_STATUS_V2 and do not inspect files." debug-opencode-spawn-fixed-v2-20260627 -w .
oma agent:status debug-opencode-spawn-fixed-v2-20260627 backend-engineer
```

Results:

```text
10.6.1
backend-engineer:crashed
backend-engineer:completed
```

Confirmed status artifact:

```text
C:\Users\visimeos\AppData\Local\Temp\subagent-debug-opencode-spawn-fixed-v2-20260627-backend-engineer.status
completed
```

## Similar Patterns

Serena scan found no OMA CLI implementation in this repository. The relevant code is in the installed OMA bundle outside the workspace. Repository workflow docs contain result/progress polling references, but no additional workspace code location with the same cleanup/status bug was confirmed.

## Upstream

Reported upstream: https://github.com/first-fluke/oh-my-agent/issues/583
