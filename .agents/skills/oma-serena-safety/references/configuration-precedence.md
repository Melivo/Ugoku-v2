# Serena Configuration Precedence

## Verified Native Serena Behavior

For current Serena versions, the effective tool timeout is:

1. `serena start-mcp-server --tool-timeout <seconds>` when provided.
2. `<home>/.serena/serena_config.yml` key `tool_timeout` otherwise.
3. Serena's built-in default when the global key is absent.

The MCP factory loads the global Serena config and then assigns the CLI value when `tool_timeout` is not `None`. Therefore the CLI option overrides the global file for that server process.

`<cwd>/.serena/project.yml` and `project.local.yml` do not currently support `tool_timeout`. `ProjectConfig` supports project fields such as `symbol_info_budget`, `language_backend`, and `line_ending`, but not the tool execution timeout. `project.local.yml` overrides supported keys from `project.yml`; it cannot introduce unsupported keys.

Consequences:

- Do not write `tool_timeout` into project Serena YAML.
- Use global `tool_timeout: 10.0` for Serena invocations without a CLI override, including CLI recovery operations.
- Use `--tool-timeout 10` for a specific MCP process when its launch command must be self-contained.
- Keeping both is intentional only when both ordinary Serena CLI calls and MCP-server calls must independently enforce the policy.

## Separate MCP Client Timeout

The MCP client's `timeout` is not Serena's `tool_timeout`. Configure both when required:

- Serena `--tool-timeout 10`: seconds allowed for a Serena tool execution.
- OpenCode `timeout: 10000`: milliseconds used by OpenCode for its local MCP operation/startup boundary.
- Other clients may use seconds, milliseconds, or separate startup and tool-call fields. Verify the client's schema before writing.

The bundled script reports candidate client files heuristically. It does not use those regex results as authority because JSONC/TOML schemas and Serena block locations differ by client. Confirm effective values with the active client's MCP listing or debug configuration before editing.

## Project Versus User Client Config

Project/user precedence belongs to the MCP client, not Serena. Do not generalize one client's merge rule to another.

Use this decision order:

1. Identify the active client.
2. Ask the client to show its effective MCP servers when it has such a command.
3. Locate the source that owns the effective Serena entry.
4. If the file is generated, find and edit its SSOT instead.
5. Apply the 10-second values only to the winning source.
6. Re-run generation/sync and inspect the effective client view.

Typical authoritative user paths include:

- OMA candidates: `<home>/.agents/mcp.json` and `<home>/.agents/mcp_config.json`
- Host SSOT: `<home>/.config/mcp/servers.yaml`
- OpenCode: `<home>/.config/opencode/opencode.jsonc` or a project OpenCode config
- Codex: `<home>/.codex/config.toml` or a project-specific source
- Claude: `<home>/.claude.json` and project entries managed by Claude

Treat paths under `<home>/.config/mcp/generated/` as generated unless proven otherwise.

## AGENTS.md Scope

Agent-instruction precedence is runtime-specific. Check both `<cwd>/AGENTS.md` and `<home>/AGENTS.md` because a runtime may load one, both, or neither. Avoid duplicate text:

- Replace the `SERENA-PLAYBOOK` managed block when present.
- Preserve equivalent existing safety guidance outside the managed block.
- Append the managed block only where no equivalent guidance exists.
- If `cwd` is the home directory, process the single path once.

## Project Language Servers

Serena reads project languages from `<cwd>/.serena/project.yml`. If `<cwd>/.serena/project.local.yml` defines `languages`, that local value overrides the base project value. Update only the winning file.

Select languages from meaningful project source files:

1. Prefer `git ls-files --cached --others --exclude-standard` so ignored files are absent.
2. Fall back to a non-symlink-following filesystem walk when Git is unavailable.
3. Exclude Serena/agent metadata, dependencies, generated output, build output, caches, and vendor trees.
4. Count recognized programming-language extensions. Do not auto-enable JSON, YAML, TOML, or Markdown LSPs merely because project metadata exists.
5. Always keep the dominant recognized language.
6. Keep a secondary language only with at least five files or at least 10% of recognized source files.
7. Order enabled languages by descending file count, then language name for deterministic ties.
8. Preserve explicitly configured backend variants (`typescript_vts`, `python_jedi`, `python_ty`, `cpp_ccls`, `csharp_omnisharp`, `ruby_solargraph`, or `php_phpactor`) when their base language remains selected.

The threshold prevents isolated helpers from starting extra language servers. For example, two documentation-generator Python scripts in a repository with 89 TypeScript files are reported as low signal and do not enable Python. A small project with two TypeScript and one Python source file keeps both because Python represents one-third of recognized source files.

If no meaningful source language exists, use `languages: []` in an already valid Serena project config. Do not write `languages:` with a null value and do not invent a fallback language. Restart Serena after changing the language list because language servers are selected during project initialization.

## Source Evidence

The behavior above is grounded in current Serena source:

- `serena/config/serena_config.py`: `SerenaConfig.tool_timeout`, global config path resolution, and `ProjectConfig` fields.
- `serena/config/serena_config.py`: `project.local.yml` overrides supported project keys, including `languages`, from `project.yml`.
- `serena/cli.py`: `--tool-timeout` is documented as an override and passed to the MCP factory.
- `serena/mcp.py`: a non-null CLI timeout is assigned after loading the default/global config.
