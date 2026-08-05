# Work Result - Pros Runtime Manifest Migration

Status: completed

Summary:
- Replaced runtime `apm.yml` documentation artifact with `runtime/pros/pros-runtime-manifest.md`.
- Added `docs/references/pros-runtime-manifest.md` and updated runtime/docs/help references to use Pros Runtime Manifest instead of obsolete Pros target-state terminology.
- Updated runtime builder, init install entries, release workflow checks, CLI status text, and tests.
- Added legacy cleanup so stale workspace `apm.yml` is backed up and removed during init/update paths.
- Added deterministic validated MCP setup details for Serena and HubSpot in the runtime manifest.

Files changed include:
- `.gitea/workflows/release.yaml`
- `runtime/pros/pros-runtime-manifest.md`
- `runtime/pros/apm.yml` removed
- `packages/pros-cli/src/init.ts`
- `packages/pros-cli/src/runtime-builder.ts`
- `packages/pros-cli/src/cli.ts`
- `packages/pros-cli/src/*test.ts`
- docs references/plans/help files

Verification passed:
- `node scripts/validate-runtime-files.js`
- `npx vitest run packages/pros-cli/src/init.test.ts packages/pros-cli/src/cli.test.ts packages/pros-cli/src/runtime-builder.test.ts`
- `npm run typecheck`
- `npm run lint`
- `npm test`
- Final QA recheck: no blocking findings.

Residual risks:
- Serena memories were reviewed and updated so Pros target-state references use Pros Runtime Manifest terminology; remaining APM mentions are Microsoft APM or legacy/historical context.
- Release artifact extension `.apm` remains existing package format terminology, separate from Pros Runtime Manifest target-state docs.
