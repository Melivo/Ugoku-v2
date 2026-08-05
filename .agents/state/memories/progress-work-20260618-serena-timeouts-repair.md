# Progress: Serena timeout repair 2026-06-18

Status: repaired, online path retained, verified through external MCP SDK, and documented.

- Serena SSOT still uses `uvx --from git+https://github.com/oraios/serena`.
- Root fix is `.serena/project.yml`: `ignore_all_files_in_gitignore: false`.
- OpenCode config was synced and reports Serena connected with the online command.
- Memory write/edit/read verification passed against the online command.
- Current chat's Serena tool connection may need an OpenCode session restart because it is stale after killing the old process.
