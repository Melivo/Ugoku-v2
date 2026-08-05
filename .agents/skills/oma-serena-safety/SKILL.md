---
name: oma-serena-safety
description: >
  Install or audit a cross-platform Serena safety playbook in project and user-home AGENTS.md files, enforce 10-second Serena/MCP timeouts, and keep project language servers limited to meaningful source languages in the current workspace. Use for Serena setup, broad-search crash prevention, timeout repair, AGENTS.md guidance, unnecessary Python or other LSP removal, project language detection, or Serena configuration precedence checks on Windows, Linux, or macOS.
---

# Serena Safety Playbook

## Scheduling

### Goal
Keep Serena searches narrowly scoped, enforce 10-second execution boundaries, and start only language servers justified by meaningful source files in the current workspace.

### Intent signature
- Add Serena safety instructions to project and user-level `AGENTS.md` files.
- Audit or repair Serena `tool_timeout`, MCP `--tool-timeout`, or client `timeout` settings.
- Determine whether a project Serena config overrides the global config.
- Detect and remove unnecessary Serena language servers, such as Python in a TypeScript-only project.
- Prevent broad Serena scans, MCP queue hangs, or repeat timeout failures.

### When to use
- Preparing Serena on Windows, Linux, or macOS.
- Repairing missing or inconsistent Serena safety guidance.
- Checking project-versus-user Serena timeout precedence.
- Standardizing a 10-second Serena/MCP timeout policy.
- Aligning `.serena/project.yml` or `project.local.yml` languages with the current codebase.

### When NOT to use
- Installing or upgrading Serena itself -> use `install-mcp-server`.
- Synchronizing a known host MCP SSOT to every client -> use `mcp-config-sync` after this skill identifies the authoritative source.
- Diagnosing language-server startup failures unrelated to timeout policy -> use `oma-debug`.

### Expected inputs
- `cwd`: project root; default to the current working directory.
- `home`: user home from `Path.home()`; override only for testing.
- `apply`: whether to write missing guidance and timeout changes.
- `client`: active MCP client when known, such as OpenCode, Codex, Claude, or Hermes.
- Project source files tracked by Git or present as non-ignored files.

### Expected outputs
- Serena safety guidance present in both applicable `AGENTS.md` files, without duplicate sections.
- Native Serena timeout effectively set to 10 seconds.
- Active MCP Serena command containing `--tool-timeout 10` and client timeout set to 10 seconds in that client's units.
- Effective Serena `languages` exactly matching meaningful source languages, with low-signal helpers reported but not enabled.
- Concise report of authoritative files, inherited values, changes, and unresolved client precedence.

### Dependencies
- Python 3.10+ and `scripts/requirements.txt` for comment-preserving YAML updates.
- Serena CLI when a missing global config must be initialized.
- `references/configuration-precedence.md` for verified Serena precedence and client rules.

### Control-flow features
- Audit before writing; use `--apply` only after identifying the active configuration source.
- Skip duplicate `AGENTS.md` guidance when equivalent safety rules already exist.
- Branch between CLI override, global Serena config, project config, and MCP-client configuration.
- Detect source languages without scanning dependency, generated, build, Serena, or agent-metadata trees.
- Stop for clarification when multiple client configs exist and the active client or SSOT cannot be established.

## Structural Flow

### Entry
1. Resolve `cwd`, the platform-independent user home, and the active MCP client if available.
2. Read `references/configuration-precedence.md` before changing timeouts or project languages.
3. Run the bundled audit without `--apply`.

### Scenes
1. **PREPARE**: Resolve exact project and home paths; avoid recursive home-directory searches.
2. **ACQUIRE**: Inspect only `AGENTS.md`, `.serena/project*.yml`, `~/.serena/serena_config.yml`, known client/SSOT paths, and bounded project source paths reported by Git or a filtered walk.
3. **REASON**: Identify effective precedence and meaningful languages. Treat `--tool-timeout` as overriding Serena's global value; treat `project.local.yml` languages as overriding `project.yml`.
4. **ACT**: Apply missing guidance, synchronize the effective project language list, set global `tool_timeout: 10.0` when needed, and patch only the active MCP source.
5. **VERIFY**: Re-run the audit, parse changed configs, and inspect the client's effective MCP listing when supported.
6. **FINALIZE**: Report which layer wins and why no redundant lower-priority setting was added.

### Transitions
- If a managed playbook block exists, replace only that block with the current canonical content.
- If equivalent non-managed Serena safety guidance exists, preserve it and do not append a duplicate block.
- If `cwd` equals the user home, process the single `AGENTS.md` path once.
- If the Serena MCP command passes `--tool-timeout 10`, that value wins for that process; retain global `tool_timeout: 10.0` only when Serena CLI calls also require the policy.
- If a project config contains `tool_timeout`, remove it after confirming the installed Serena schema because current Serena does not support that project key.
- If `project.local.yml` defines `languages`, update only that winning override; otherwise update `project.yml`.
- Always include the dominant source language. Include another language only when it has at least five files or at least 10% of recognized source files.
- Preserve a configured backend variant such as `typescript_vts` or `python_jedi` when its base language remains selected.
- Ignore `.agents`, `.serena`, dependencies, generated output, build output, caches, and vendor trees during language detection.
- If a generated client fragment has an upstream SSOT, edit the SSOT and run its sync mechanism instead of editing the generated file.

### Failure and recovery
| Failure | Recovery |
|---------|----------|
| Multiple project and home MCP configs exist | Identify the active client and its merge rules; do not guess which file wins. |
| Global Serena config is missing | Run `serena init`, then set `tool_timeout: 10.0`; never create an incomplete YAML containing only the timeout. |
| Serena MCP times out during verification | Retry once with a narrower request, then use the Serena CLI fallback from the workspace. |
| Existing MCP process remains wedged | Stop the stale `serena ... start-mcp-server` process and restart the client before retesting. |
| YAML/JSON/TOML cannot be parsed | Preserve the file, report the parse failure, and repair syntax before changing timeout values. |
| A helper script would add an otherwise irrelevant LSP | Report it under `ignored_low_signal`; do not enable that language unless it reaches the documented threshold. |
| No meaningful source language is detected | Write `languages: []` only to an existing valid project config; do not invent a fallback language. |
| `cwd` resolves to the user home or filesystem root | Refuse the audit; require a narrower project directory. |

### Exit
- Success: both instruction scopes are covered, effective timeouts resolve to 10 seconds, and the winning project language list matches meaningful source languages.
- Partial success: guidance is installed, but ambiguous client precedence or an unavailable Serena CLI is reported with exact paths.
- Failure: no unsafe config is written and the blocking parse, ownership, or precedence ambiguity is explicit.

## Logical Operations

### Actions
| Action | SSL primitive | Evidence |
|--------|---------------|----------|
| Resolve project and home files | `SELECT` | Explicit `cwd`, `Path.home()`, known config paths |
| Audit safety guidance | `VALIDATE` | `AGENTS.md` contents and managed markers |
| Determine timeout precedence | `INFER` | CLI args, Serena global config, installed schema, client config |
| Detect meaningful source languages | `INFER` | Git files or filtered filesystem walk, extension counts, selection threshold |
| Install managed guidance | `WRITE` | `SERENA-PLAYBOOK:START/END` block |
| Synchronize language servers | `WRITE` | Effective `.serena/project.yml` or `project.local.yml` language block |
| Repair authoritative timeout | `WRITE` | Serena global config or active MCP SSOT |
| Re-run audit | `VALIDATE` | JSON report from `serena_safety.py` |
| Report effective values | `NOTIFY` | Paths, layers, values, and skipped duplicates |

### Tools and instruments
- `python scripts/serena_safety.py --cwd <project> --home <home>` for read-only audit.
- `python scripts/serena_safety.py --cwd <project> --home <home> --apply` for managed guidance and native global timeout repair.
- Client-native commands such as `opencode mcp list`, `codex mcp list`, or `claude mcp list` only for the installed active client.
- `references/configuration-precedence.md` for authoritative layering rules.

### Canonical workflow path
1. Run `python scripts/serena_safety.py --cwd <project> --home <home>` and inspect its JSON report.
2. Confirm the active MCP client and whether a reported config is authoritative, generated, or inactive.
3. Inspect `native_serena.languages`, including `counts` and `ignored_low_signal`; confirm exceptional generated directories are not being treated as source.
4. Run the script with `--apply` to install missing guidance, synchronize the winning project language list, and repair the global native timeout.
5. Patch the active MCP SSOT so Serena receives `--tool-timeout 10` and the client uses 10 seconds in its required units; do not patch inactive duplicates.
6. Run the SSOT's sync command if one exists.
7. Re-run the script without `--apply`, parse changed files, restart Serena when languages changed, and verify the active client's effective MCP listing.

### Resource scope
| Scope | Resource target |
|-------|-----------------|
| `CODEBASE` | `<cwd>/AGENTS.md`, `<cwd>/.serena/project.yml`, known project MCP configs |
| `USER_DATA` | `<home>/AGENTS.md`, `<home>/.serena/serena_config.yml`, user MCP configs |
| `PROCESS` | Serena CLI and active MCP-client verification commands |

### Preconditions
- The project root and user home are resolved without a broad Serena search.
- The active MCP client or authoritative SSOT is known before client config writes.
- Existing files are readable and unrelated user content can be preserved.

### Effects and side effects
- May create or append `AGENTS.md` with a managed Serena playbook block.
- May initialize Serena's complete global config and set `tool_timeout: 10.0`.
- May replace only the effective Serena project `languages` block and require a Serena restart.
- May update one authoritative MCP source and regenerate client fragments through an existing sync tool.
- Does not terminate processes unless a wedged Serena process is confirmed.

### Guardrails
1. Never run broad Serena searches over a user home, broad repository root, generated tree, or binary directory.
2. Never launch multiple broad Serena calls in parallel; expand narrow searches sequentially.
3. Never write `tool_timeout` into `.serena/project.yml` or `project.local.yml` unless the installed Serena schema explicitly supports it.
4. Never edit generated MCP fragments when an upstream SSOT exists.
5. Never create a partial `~/.serena/serena_config.yml`; initialize it through Serena first.
6. Never overwrite an entire `AGENTS.md`; replace only this skill's managed block or append one when equivalent guidance is absent.
7. Never assume project client config overrides user config across all clients; verify the active client's documented merge behavior.
8. Keep MCP client timeout units explicit: OpenCode JSON uses milliseconds (`10000`), while CLI options such as Serena's `--tool-timeout` use seconds (`10`).
9. Never enable a language merely because a dependency, generated artifact, managed agent skill, or isolated low-signal helper uses its extension.
10. Never edit both project language files when `project.local.yml` already supplies the effective `languages` override.
11. Never replace a relevant explicitly configured backend variant with the default backend solely during language cleanup.
12. Treat MCP candidate-file parsing as discovery only; confirm effective values through the active client before writing.
13. Require audit preflight before `--apply`; write each file atomically and preserve its existing LF/CRLF style.
14. Snapshot every managed file before `--apply` and roll all of them back when initialization, parsing, or writing fails.

## References
- Serena configuration precedence: `references/configuration-precedence.md`
- Audit and managed-section utility: `scripts/serena_safety.py`
