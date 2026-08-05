# Implementation Progress

Status: completed

Implemented Phase 2:
- Added 21 generic business skills under `runtime/pros/.agents/skills/`.
- Vendored utility skills: `doc`, `install-mcp-server`, `mcp-config-sync`, `playwright`, `security-best-practices`, `skill-creator`, `skill-installer`.
- Removed Python `__pycache__` folders from vendored utility skills.
- Adjusted key utility skill docs away from hardcoded `%USERPROFILE%/.agents/skills` and `$CODEX_HOME/skills` paths toward current runtime workspace paths.
- Added 13 generic workflows under `runtime/pros/.agents/workflows/`.
- Added `runtime/pros/pros-Hilfe/skill-katalog.md`.
- Updated `ALLOWED_SKILLS`, `ALLOWED_WORKFLOWS`, and runtime AGENTS guidance in `packages/pros-cli/src/runtime-builder.ts`.
- Added runtime-builder regression assertions for business skills, utility resources, workflow shims, and catalog.
- Fixed runtime source resolution so package-level local dev commands can find repo-root `runtime/pros` when run from `packages/pros-cli`.

Verification:
- `npm test` passed in `packages/pros-cli`.
- `npm run typecheck` passed in `packages/pros-cli`.
- `npm run lint` passed in `packages/pros-cli`.

IMPL_GATE: passed.
