# Work Result

## Current Runtime Manifest Status

The old `apm.yml` runtime document has been superseded by `runtime/pros/pros-runtime-manifest.md`.

Current behavior:
- Runtime projection installs `pros-runtime-manifest.md`.
- `pros init` backs up and removes stale workspace `apm.yml`.
- Release workflow rejects legacy `dist/runtime/apm.yml` and requires `dist/runtime/pros-runtime-manifest.md`.
- Use `Pros Runtime Manifest` for Pros target-state documentation.
- Use `APM` only for Microsoft Agent Package Manager or legacy release bundle naming.

## Historical Note: Legacy Windows Path Validation (2026-05-05)

The previous validation found the old `apm.yml` portable on Windows. That result is retained only as historical context because `apm.yml` is no longer the Pros runtime documentation source.
