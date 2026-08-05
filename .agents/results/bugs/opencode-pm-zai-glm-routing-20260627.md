# OpenCode PM GLM Routing Debug - 2026-06-27

## Symptom

Native OpenCode `task(subagent_type="pm-planner")` failed when the PM agent was routed to Z.ai GLM:

```text
Model not found: zai/glm-5.2. Did you mean: glm-5.2?
Model not found: glm-5.2/.
```

## Root Cause

Two issues overlapped:

1. Earlier generated PM agent frontmatter used invalid model slugs such as `zai/glm-5.2` or bare `glm-5.2` instead of the real OpenCode catalog slug `zai-coding-plan/glm-5.2`.
2. The running OpenCode Desktop/native `task` host kept stale model resolution until OpenCode was restarted. `opencode debug agent pm-planner` and `opencode run -m zai-coding-plan/glm-5.2 --variant high` were already correct before the native task host succeeded.

## Fix Applied

- Set PM agent frontmatter to the documented full OpenCode model slug:

```yaml
model: zai-coding-plan/glm-5.2
variant: high
mode: subagent
```

- Applied this to both:
  - `.opencode/agents/pm-planner.md`
  - `C:\Users\visimeos\.opencode\agents\pm-planner.md`
- Set `.agents/oma-config.yaml` PM routing to `opencode-zai-coding-plan/glm-5.2` with `effort: high`.
- Renamed OpenCode model aliases to preserve full provider IDs:
  - `opencode-zai-coding-plan/glm-5.2`
  - `opencode-kimi-for-coding/k2p7`
- Fixed `research-explorer` from invalid `kimi/k2p7` to `kimi-for-coding/k2p7` in workspace and userhome agent files.
- Removed stale workspace temp wrapper `.opencode/agents/oma-spawn-pm-ultrawork-20260627-pros-deterministic-setup-test.md`.

## Verification

- `opencode models zai-coding-plan --verbose` shows `glm-5.2` variants `high` and `max`.
- `opencode debug agent pm-planner` resolves `providerID: zai-coding-plan`, `modelID: glm-5.2`, `variant: high`.
- `opencode run -m zai-coding-plan/glm-5.2 --variant high ...` returned `STATUS ok`.
- After restarting OpenCode Desktop, native `task(subagent_type="pm-planner")` returned `STATUS: ok`.
- `opencode debug agent` was run for all agent markdown names in workspace and userhome; all parsed successfully and every explicit model is listed by `opencode models`.

## Similar Patterns Found

- `research-explorer` had invalid `kimi/k2p7`; fixed to `kimi-for-coding/k2p7`.
- Workspace regenerated `.opencode/agents/*.md` files may omit model frontmatter, but effective OpenCode resolution still merged userhome model fields correctly. To avoid ambiguity, workspace agent frontmatter was manually restored with explicit `model`/`variant` fields for all model-routed agents.

## PM Effort Decision

Default PM thinking effort remains `high`, not `max`. PM work usually involves structured planning, decomposition, acceptance criteria, and dependency analysis. `max` is reserved for exceptional high-ambiguity planning with many cross-domain tradeoffs because it increases latency and reasoning budget and can over-plan routine PM tasks.
