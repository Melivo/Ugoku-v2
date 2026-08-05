# Architecture Review: Dev `.agents` vs pros Runtime Separation

## Problem

The repository currently mixes two different ownership domains:

- Root `.agents/` is the OMA development/control-plane environment for repository work.
- End-user pros runtime needs its own curated `.agents/` projection for customer case folders.

The current implementation violates that boundary because customer-facing `pro-select-*` skills live under root `.agents/skills/`, and `packages/pros-cli/src/runtime-builder.ts` reads from root `.agents` and root `.serena` to produce `dist/runtime/`. `initLocal()` has the same boundary leak in local dev mode.

## Constraints and Quality Attributes

- Root `.agents/` must remain safe for developer OMA workflows only.
- Customer Pro Select skills must not be installed into or sourced from root `.agents`.
- Release artifacts must still contain end-user `.agents/skills/pro-select-*` and `.agents/pros-config.yaml`.
- Runtime packaging must use an explicit projection source, not raw source `.agents` or source `.serena`.
- The solution must be Windows-compatible and preserve the current `pros init` end-user layout.
- The immediate goal is boundary correctness, not OAuth, license management, or release-please automation.

## Existing Architecture

Key modules:

- `packages/pros-cli/src/runtime-builder.ts` builds `dist/runtime/`.
- `packages/pros-cli/src/init.ts` initializes runtime folders and has a local dev fallback.
- `.gitea/workflows/release.yaml` invokes `buildRuntimeProjection({ sourceDir: '.', outputDir: 'dist/runtime', ... })`.
- Root `.agents/` contains both OMA development skills and customer `pro-select-*` skills.

Current coupling points:

- `runtime-builder.ts` copies from `sourceDir/.agents/skills`, `sourceDir/.agents/workflows`, `sourceDir/.agents/rules`, and `sourceDir/.serena/memories`.
- `initLocal()` copies `pro-select-*` from `process.cwd()/.agents/skills`.
- Release workflow passes `sourceDir: '.'`, making repository root the runtime source.

Primary architecture risk:

- Any future dev skill/config/memory under root `.agents` or `.serena` can accidentally leak into runtime packaging if allowlists change or logic regresses.

## Method

Selected method: Design-Twice.

Reason: This is a durable boundary and ownership decision. It affects release packaging, local dev behavior, tests, and future repo evolution. A lighter recommendation would risk anchoring on the first obvious directory layout without testing alternatives.

## Options

### Option A: Dedicated Runtime Source Tree `runtime/pros/`

Create a separate source tree for customer runtime inputs:

```text
runtime/pros/
  .agents/
    skills/pro-select-*/
    workflows/
    rules/
  .serena/memories/
  pros-Hilfe/
```

Root `.agents/` remains developer-only. `runtime-builder.ts` reads from `runtime/pros` and generates `dist/runtime/`.

Pros:

- Strongest ownership boundary.
- Easy CI guard: root `.agents/skills/pro-select-*` must not exist.
- Runtime source is visible, reviewable, and versioned.
- Release provenance becomes clear: `runtime/pros` -> `dist/runtime` -> ZIP.
- Supports future customer-specific workflow text without touching dev workflows.

Cons:

- Some files initially duplicate root dev workflows/rules until customer-specific versions are refined.
- Requires updating builder, local dev fallback, tests, and docs.

### Option B: Keep Root `.agents`, Add Strict Allowlist and Guard

Leave `pro-select-*` under root `.agents`, but enforce explicit allowlists and CI checks to prevent non-allowed files from shipping.

Pros:

- Smallest immediate file movement.
- Minimal runtime-builder changes.

Cons:

- Does not satisfy the user's stated boundary: root `.agents` would still contain customer skills.
- Keeps conceptual ambiguity: is `.agents` dev SSOT or customer source?
- Future contributors can still confuse dev and runtime ownership.
- CI guards become more complex because allowed customer files intentionally live in the forbidden area.

### Option C: Generate Runtime Skills from Package-Embedded Templates

Move customer runtime templates under `packages/pros-cli/templates/runtime/` and ship them with the npm package. Release artifacts are generated from packaged templates.

Pros:

- Runtime source colocated with CLI package.
- Easier npm package self-containment.

Cons:

- Blurs product content with CLI implementation code.
- Makes non-code Pro Select skill edits look like package-code changes.
- Less natural for future richer runtime content and documentation assets.
- Still needs a clear external runtime source if content grows.

## Tradeoff Comparison

| Criterion | Option A: `runtime/pros` | Option B: root allowlist | Option C: package templates |
|---|---|---|---|
| Boundary clarity | High | Low | Medium |
| Satisfies user rule | Yes | No | Mostly |
| Implementation cost | Medium | Low | Medium |
| Future change cost | Low | High | Medium |
| Release provenance | High | Medium | Medium |
| Team cognitive load | Low after migration | High | Medium |
| Risk of accidental leakage | Low with CI guard | Medium | Low |

## Recommendation

Choose Option A: create `runtime/pros/` as the customer runtime source tree.

Required architecture rules:

- Root `.agents/` is only for OMA/dev control-plane content.
- Customer Pro Select skills live only under `runtime/pros/.agents/skills/pro-select-*`.
- Root `.serena/` remains development memory and is not a runtime source.
- Runtime memory templates live under `runtime/pros/.serena/memories/`.
- `dist/runtime/` is generated only from `runtime/pros` plus generated files such as `.agents/pros-config.yaml` and `AGENTS.md`.
- `initLocal()` must also use `runtime/pros` as local dev source, not root `.agents`.
- CI must fail if root `.agents/skills/pro-select-*` appears again.

## Risks

- If current root workflows are copied into `runtime/pros` unchanged, customer runtime may still contain OMA-oriented instructions. Mitigation: copy only as a temporary compatibility baseline and schedule customer-specific workflow simplification.
- Existing docs and memories mention `.agents/skills/pro-select-*` generically. Some references may need clarifying as runtime-layout references, not source-layout references.
- Tests must cover both absence from root `.agents` and presence in generated runtime, or the separation can regress silently.

## Assumptions

- `runtime/pros` is acceptable as a top-level product/runtime source directory.
- The immediate release still needs the same four Pro Select skills.
- Root `.serena/memories/domain/pro_select_*` may remain as developer memory, but must stop being a runtime packaging source.
- Runtime workflows/rules can initially be copied from existing curated files, then refined later.

## Validation Steps

- Static boundary check: no `.agents/skills/pro-select-*` exists.
- Builder test: generated runtime contains `.agents/skills/pro-select-*`.
- Builder test: generated runtime contains `.agents/pros-config.yaml`.
- Builder test: generated runtime does not contain `.agents/oma-config.yaml`.
- Local dev test: `pros init` local fallback uses `runtime/pros`, not root `.agents`.
- Release workflow check: `buildRuntimeProjection` is invoked with `runtimeSourceDir` or equivalent, not raw root as the runtime content source.

## Handoff

Proceed to `/plan` or continue the existing Ultrawork PLAN_GATE with this architecture decision as the approved target. Implementation should not start until the user confirms this recommendation.
