# QA Result — QNAP MCP Assistant readiness/token path
Status: FAIL

Automated verification:
- npm audit: PASS, 0 vulnerabilities
- npm run lint: PASS
- npm run typecheck: PASS
- Targeted Vitest: PASS, 4 files / 67 tests
- Serena CLI index-file --verbose: completed for requested files

Findings:
- HIGH packages/pros-cli/src/mcp-qnap-assistant.ts:46-58 — QNAP token is injected into the environment of an unpinned `npx -y mcp-remote` child. Config/argv redaction is good, but secret-safety is not sufficient because npm/npx package resolution/install/runtime receives the bearer token. Fix by pinning mcp-remote as a runtime dependency, executing the local vendored entrypoint, and passing only an allowlisted minimal env with the token.
- LOW packages/pros-cli/src/qnap-files.ts:326-333 — QNAP status returns arbitrary client success message; future client implementations could echo credential context. Return a static success message or sanitize.

Report written: .agents/results/result-qa-qnap-work-microsoft-graph-oauth-qnap-readiness-20260708.md