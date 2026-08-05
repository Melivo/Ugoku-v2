# Tech Stack Reference

## Framework Version And Core API

This repository uses TypeScript 5.8 on Node.js 20+ with ES modules and `moduleResolution: NodeNext`. There is no HTTP backend framework. The backend-like surface is a CLI/service-module architecture:

- `packages/pros-cli/src/cli.ts` owns argument parsing, process I/O, and exit codes.
- Service modules such as `init.ts`, `update.ts`, `doctor.ts`, `workspace.ts`, and `summary.ts` return structured values and user-facing messages.
- Low-level modules such as `auth.ts`, `gitea.ts`, `manifest.ts`, `zip.ts`, and `runtime-builder.ts` avoid depending on CLI output handling.

## ORM/DB Library And Usage

No ORM or database library is used. Persistent state is file-based:

- CLI auth config is stored outside business workspaces by `auth.ts`.
- Installer state is written to `.pros/state.json` after successful runtime installation.
- Runtime/business context is stored in workspace files and `.serena/memories`, not a database.

## Validation Library

No external validation library is used. Validation is implemented with TypeScript interfaces, explicit checks, and small parser helpers.

Use manual guards for external inputs such as JSON files, manifests, release tags, CLI arguments, paths, and network responses. Do not assume parsed JSON matches its TypeScript type.

## Migration Tool

No schema migration tool is used. File-format changes should be handled explicitly in the owning service module and covered by regression tests.

If `.pros/state.json` or `.agents/pros-config.yaml` changes, preserve installed-user compatibility only when existing persisted installations require it.

## Test Framework

Vitest is the test framework. Tests live beside source files as `*.test.ts` under `packages/pros-cli/src/` plus repository-level tests in `tests/`.

Relevant commands:

```bash
npm test
npm run typecheck
npm run lint
npm run release:dry-run
```

## Linter/Formatter

Biome is used for linting/formatting checks. The root lint script checks package metadata, TypeScript config, CLI sources, and repository tests.

Follow existing conventions:

- ESM imports with explicit `.js` extensions for local TypeScript modules.
- Node built-ins imported through `node:` specifiers.
- Strict TypeScript settings from `tsconfig.base.json`.
- Service modules should not write to stdout/stderr directly.
