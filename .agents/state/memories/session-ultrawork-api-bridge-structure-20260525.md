# Ultrawork Session: API Bridge Structure

Session start: 2026-05-25
Workflow: ultrawork
User request: first implement the structure for first-party API bridge config/install model for integrations without validated MCP servers.
Runtime vendor detection: Codex-like/OpenCode environment because `apply_patch` is available. Native role-subagent dispatch is not verified, so inline work plus Task subagents will be used.

Phase 0 status: initialized. Loaded ultrawork workflow, oma-coordination core rules, context-loading, memory protocol, vendor detection, multi-review protocol, quality principles, and phase gates.

Phase 1 PLAN status: passed. PM plan produced requirements, assumptions, alternatives, API/data contracts, prioritized tasks, and reviews. User's `setze es um` is treated as confirmation. Scope: first-party API bridge structure only; no OAuth token exchange, no credential persistence implementation.

Phase 2 IMPL status: implemented. Added provider registry/capabilities/policies, global non-secret profiles loader, case-local allowlist loader, secret-key rejection, readiness merge, `pros integrations profile list`, `pros integrations preflight`, Pros Runtime Manifest config model, tests, and plan artifacts. Focused checks passed: typecheck, lint, targeted integrations/CLI tests, runtime validation.

Phase 3 VERIFY status: passed after remediation. QA initially found HIGH multi-profile allowlist selection issue and MEDIUM allowlist shape validation issue. Fixed by selecting allowed profiles before readiness merge, validating allowlist shapes, strengthening preflight assertions, and updating Pros Runtime Manifest test status. Targeted tests/typecheck/lint/runtime validation pass.

Phase 4 REFINE status: passed after remediation. Split provider registry into `integration-registry.ts`, kept API config in `integration-config.ts`, re-exported through `integrations.ts`, and split large validation/status functions. Refine re-check passed with no blocking findings.

Phase 5 SHIP status: passed pending user final approval. Initial ship review found MEDIUM secret-key validation gap for names such as `bearerToken`; fixed by normalized secret fragments and regression test. Final verification passed: typecheck, lint, full tests (64 passed, 1 skipped), audit, runtime validation, release dry-run, plan JSON parse, and diff check with only CRLF warnings.
