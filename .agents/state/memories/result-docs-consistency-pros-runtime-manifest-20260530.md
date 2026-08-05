# Docs Consistency Result - Pros Runtime Manifest (2026-05-30)

Status: completed

Scope:
- README, end-user handbook source, MCP/Credentials docs, references, work/design plans, runtime workflow, and Serena memories.

Actions:
- Verified README, `docs/pros-hilfe-src/endnutzerhandbuch.md`, `docs/MCP-CREDENTIALS.md`, and `runtime/pros/.agents/workflows/werkzeuge-mcp-einrichtung.md` use consistent Pros Runtime Manifest terminology.
- Updated work/design docs so Pros target-state language uses `Pros Runtime Manifest` / `pros-runtime-manifest.md`, not operational APM terms.
- Reviewed `.serena/memories` and updated stale operational APM references to Pros Runtime Manifest terminology.
- Renamed outdated memories:
  - `design/pros-apm-runtime-distribution-constraints` -> `design/pros-runtime-manifest-distribution-constraints`
  - `qa/apm-windows-path-validation-20260505` -> `qa/pros-runtime-manifest-windows-path-validation-20260505`
- Marked remaining `apm.yml` mentions as legacy/historical or Microsoft APM boundary context.

Checks:
- `oma docs verify --json --no-urls` could not run because `oma` is not on PATH in this environment.
- Deterministic grep checks found no remaining operational `APM-Zielzustand`, `Runtime/APM`, `APM Projection`, `APM-Dokumentation`, `APM/API`, or `runtime/APM` wording in docs/memories.
- Key documentation path existence check passed.

Remaining accepted references:
- Current migration plan and reference docs intentionally mention Microsoft APM and old `runtime/pros/apm.yml` to explain the migration boundary.
- Serena memories intentionally retain some legacy `apm.yml` mentions only when explicitly marked historical or as negative-release/test context.
