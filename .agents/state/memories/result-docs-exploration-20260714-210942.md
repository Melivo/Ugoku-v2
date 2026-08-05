# Docs curation result — exploration 20260714-210942

Status: completed

Summary:
- Updated only `docs/plans/designs/005-pros-mcp-client-configuration.md` at the two requested stale areas around lines 224 and 235.
- Aligned the prose with the amended contract: Serena is outside `pros mcp configure`; `pros init` may create or maintain local `.serena/project.yml`.
- Preserved existing architectural history and unrelated content.

Files changed:
- `docs/plans/designs/005-pros-mcp-client-configuration.md`

Targeted search:
- Confirmed no remaining `Serena becomes an AnythingLLM target` / `user-home project root` wording in the target file.
- Confirmed the target file still states OpenCode-only local Office config with `cwd: "."` and AnythingLLM `unsupported_client_capability` without config writes.

Docs verification:
- Command: `oma docs verify "docs/plans/designs/005-pros-mcp-client-configuration.md" --json`
- Before: `scannedDocs=1`, `totalRefs=7`, `skippedCount=0`, `broken=2`
- After: `scannedDocs=1`, `totalRefs=9`, `skippedCount=0`, `broken=2`
- Remaining broken refs are pre-existing/out-of-scope environment-placeholder examples:
  - line 25 `%USERPROFILE%/.config/pros/mcp/managed-state.json`
  - line 27 `%APPDATA%/anythingllm-desktop/storage/plugins/anythingllm_mcp_servers.json`

Acceptance criteria checklist:
- [x] Modified only the requested docs file.
- [x] Updated the two stale areas around lines 224 and 235.
- [x] Reflected that `pros init` may create local `.serena/project.yml`.
- [x] Reflected that `pros mcp configure` never manages Serena.
- [x] Preserved the existing OpenCode Office `cwd: "."` and AnythingLLM `unsupported_client_capability` contract.
- [x] Ran targeted search for the requested contract terms.
- [x] Ran targeted `oma docs verify` for the file and recorded exact results.
