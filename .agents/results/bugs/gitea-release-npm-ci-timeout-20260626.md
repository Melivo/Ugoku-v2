# Gitea Release Workflow Failed on npm ci Timeout

Date: 2026-06-26

## Symptom

Gitea Actions showed `release.yaml #119` as failed for tag `pros-v0.5.18`.

- API run ID: 224
- Job ID: 225
- Job name: `build-and-release`
- Commit: `e0cc63a`

## Root Cause

The job failed before release creation, asset upload, or npm publish. Gitea MCP job logs showed the failure at the `Install dependencies` step:

```text
npm error code ETIMEDOUT
npm error syscall read
npm error network read ETIMEDOUT
```

The workflow used plain `npm ci`, which was vulnerable to transient registry/network read timeouts on the runner. The same un-hardened install pattern existed in `.gitea/workflows/ci.yaml`.

## Fix Applied

Both `.gitea/workflows/release.yaml` and `.gitea/workflows/ci.yaml` now run `npm ci` with npm retry and fetch timeout flags:

```text
npm ci --fetch-retries=5 --fetch-retry-factor=2 --fetch-retry-mintimeout=20000 --fetch-retry-maxtimeout=120000 --fetch-timeout=300000
```

## Regression Test

`tests/release-workflow.test.ts` now verifies that both Gitea workflow install steps use retry-tolerant npm commands.

## Similar Patterns

Serena `search_for_pattern` found no remaining `.gitea/workflows/*.yaml` `npm ci` commands without retry flags.

## Verification

- `npm test -- tests/release-workflow.test.ts` passed.
- Gitea MCP confirmed the existing `pros-v0.5.18` release has all expected assets.
- The release artifact state was complete; the red status was the workflow run status.
