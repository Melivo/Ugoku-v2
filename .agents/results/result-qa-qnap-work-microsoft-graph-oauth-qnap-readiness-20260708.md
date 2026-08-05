# QA Result — QNAP MCP Assistant Token-/Readiness-Pfad

## Review Result: FAIL

### Summary
- Scope reviewed: `mcp-client-config.ts`, `mcp-qnap-assistant.ts`, `qnap-files.ts` and requested tests.
- Automated checks: `npm audit` PASS (0 vulns), `npm run lint` PASS, `npm run typecheck` PASS, targeted Vitest PASS (4 files / 67 tests).
- Serena MCP timed out on `initial_instructions`; Serena CLI `serena project index-file ... --verbose` completed for all requested files.
- Redaction in client config/status paths is mostly sound: no token in OpenCode/AnythingLLM config, no token in argv, credential target is non-secret.
- Blocking issue: the wrapper still gives the QNAP token to an unpinned `npx mcp-remote` execution path.

### CRITICAL
- None.

### HIGH
- `packages/pros-cli/src/mcp-qnap-assistant.ts:46-58` — `runQnapMcpAssistantBridge()` spawns `npx -y mcp-remote` while `getChildEnv()` injects `PROS_QNAP_MCP_ASSISTANT_TOKEN` into the same child environment. `mcp-remote` is not pinned in `packages/pros-cli/package.json` / lockfile, so `npx` may resolve/download latest code and dependency install/runtime code receives the QNAP bearer token. This is redaction-safe for config/argv, but not secret-safe against supply-chain/install-time exposure. — Fix: add a pinned runtime dependency and execute the local vendored entrypoint with a minimal allowlisted env; never run `npx`/npm resolution with the QNAP token present.

  ```ts
  // package dependency: "mcp-remote": "0.1.38" (exact) + lockfile update
  import { createRequire } from "node:module";

  const require = createRequire(import.meta.url);

  function getMcpRemoteCommand(): { command: string; argsPrefix: string[] } {
    const pkg = require.resolve("mcp-remote/package.json");
    return {
      command: process.execPath,
      argsPrefix: [path.join(path.dirname(pkg), "dist", "proxy.js")],
    };
  }

  function getChildEnv(token: string): NodeJS.ProcessEnv {
    const env: NodeJS.ProcessEnv = {
      PATH: process.env.PATH,
      SystemRoot: process.env.SystemRoot,
      TEMP: process.env.TEMP,
      TMP: process.env.TMP,
      HTTPS_PROXY: process.env.HTTPS_PROXY,
      HTTP_PROXY: process.env.HTTP_PROXY,
      NO_PROXY: process.env.NO_PROXY,
      NODE_EXTRA_CA_CERTS: process.env.NODE_EXTRA_CA_CERTS,
      [QNAP_TOKEN_ENV]: token,
    };
    if (process.allowedNodeEnvironmentFlags.has("--use-system-ca")) {
      env.NODE_OPTIONS = "--use-system-ca";
    }
    return env;
  }
  ```

### MEDIUM
- None.

### LOW
- `packages/pros-cli/src/qnap-files.ts:326-333` — `getQnapStatus()` returns `status.message` from the injected QNAP client. The current test client is safe, but the boundary is not defensive: a future HTTP client that echoes request context could leak `credentialSecret` in a success message. — Fix: return a static success message or sanitize client text before returning it.

  ```ts
  await (options.client ?? unavailableClient()).status({
    endpoint: resolved.endpoint,
    credentialSecret: resolved.credentialSecret,
  });
  return result(true, "ready", "QNAP status checked.", {
    profileId: resolved.profile.profileId,
    endpoint: resolved.endpoint,
  });
  ```

## Runtime / Tool Verification Results
| Check | Result |
|---|---|
| `npm audit` | PASS — 0 vulnerabilities |
| `npm run lint` | PASS |
| `npm run typecheck` | PASS |
| Targeted Vitest (`mcp-client-config`, `mcp-qnap-assistant`, `qnap-files`, `cli`) | PASS — 67 tests |
| Serena CLI index-file for requested files | PASS |

## Files Changed by QA
- No source code changed.
- Added this QA report under `.agents/results/`.
- Wrote Serena memory `progress-qa-qnap-work-microsoft-graph-oauth-qnap-readiness-20260708`.

## Acceptance Criteria Checklist
- [x] All requested files reviewed.
- [x] Security reviewed first, with secret-safety emphasis.
- [x] Findings include file:line, severity, description, remediation code.
- [x] Automated checks run before final verdict.
- [x] No source code modified in first QA wave.
- [ ] PASS readiness gate — blocked by HIGH finding above.

## Follow-up Verification Recommendations
1. After replacing `npx` with a pinned local `mcp-remote`, add tests asserting the spawned command is not `npx`/`npx.cmd`, args do not contain the token, and env is allowlisted.
2. Add a CLI regression test for `pros mcp qnap token set --stdin` confirming stdout/stderr never include the submitted token.
3. Add a `qnap-files` regression test where the mock status client returns the credential in its message and assert the public result remains redacted.
