# Docs Remediation Result — 20260714-210942

## Status

PASS with out-of-scope drift noted.

## Summary

Updated the Pros global MCP runtime documentation and delivered end-user runtime guidance so Serena is no longer described as Pros-managed global MCP configuration. The authoritative contract now states:

- `pros init` may create/maintain local `.serena/project.yml` as workspace/developer configuration.
- `pros mcp configure` must not read, write, install, sync, repair, or manage Serena in OpenCode or AnythingLLM global config.
- OpenCode Office MCPs use global entries with `cwd: "."` and `--workspace-mode client-context`.
- AnythingLLM Office includes return/report `unsupported_client_capability` and leave config unchanged.

## Files changed in this remediation

- `.agents/results/api-contracts/pros-global-mcp-runtime-20260714.md`
- `docs/CLI-MCP-COMMANDS.md`
- `docs/MCP-CREDENTIALS.md`
- `docs/plans/designs/005-pros-mcp-client-configuration.md`
- `docs/plans/work/031-pros-global-mcp-runtime.md`
- `runtime/pros/pros-runtime-manifest.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/mcp-architecture.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/debugging.md`
- `runtime/pros/.agents/skills/install-mcp-server-pros/SKILL.md`
- `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md`

## Checked paths

- `runtime/pros/**/*.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md`
- `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung/resources/*.md`
- `runtime/pros/.agents/skills/install-mcp-server-pros/SKILL.md`
- `runtime/pros/.agents/skills/mcp-config-sync-pros/SKILL.md`
- `docs/CLI-MCP-COMMANDS.md`
- `docs/MCP-CREDENTIALS.md`
- `docs/plans/designs/005-pros-mcp-client-configuration.md`
- `docs/plans/work/031-pros-global-mcp-runtime.md`
- `tests/mcp-config.test.ts`
- `packages/pros-cli/src/mcp-client-config.test.ts`
- `packages/pros-cli/src/cli.test.ts`

## Commands run

- `oma docs verify --json`
- `git diff --cached --name-only; git diff --name-only HEAD~1..HEAD`
- Grep runtime/docs/tests for `Serena|serena|project-from-cwd|mcp configure|MCP`.
- Grep runtime/docs for stale contradictory claims: `pros mcp configure.*Serena|Serena.*pros mcp configure|Serena.*validated|--project-from-cwd|global.*Serena|Serena als global|CWD-Serena`.
- `npm test -- --run tests/mcp-config.test.ts packages/pros-cli/src/mcp-client-config.test.ts packages/pros-cli/src/cli.test.ts`
- `git status --short`
- `git diff -- ...`

## Verification

- Targeted tests: PASS — 3 files, 77 tests.
- `oma docs verify --json`: ran before and after. It still reports pre-existing repository-wide broken refs unrelated to this remediation, including historical `.serena/memories/**`, old plan links, and generic runtime skill examples. In-scope stale Serena/Pros-managed global MCP wording was remediated.
- Delivered runtime grep: no remaining runtime claim that Serena is a Pros-managed global MCP target; remaining runtime Serena mentions are either local memory paths or explicit developer-local/non-managed guardrails.

## Out-of-scope drift / TODO

- Historical plans `014`, `015`, `016`, and `018` still mention local Serena `--project-from-cwd` smoke-test behavior. They document prior/debug/local-dev behavior and were not updated except where current contract docs required it.
- Repository-wide doc ref drift remains in `oma docs verify --json`; not fixed because unrelated to this QA remediation scope.

## Acceptance criteria checklist

- [x] Plan updated to reflect explicit user decision.
- [x] API contract written under `.agents/results/api-contracts/`.
- [x] Delivered runtime workflow updated.
- [x] Referenced runtime skills/resources updated, including `mcp-config-sync-pros` and `install-mcp-server-pros`.
- [x] Office MCP contract states OpenCode `cwd: "."` plus `--workspace-mode client-context`.
- [x] AnythingLLM Office includes documented as `unsupported_client_capability` with unchanged config.
- [x] Local `pros init` Serena project behavior preserved.
- [x] Tests checked; no test edits were needed by this docs remediation.
