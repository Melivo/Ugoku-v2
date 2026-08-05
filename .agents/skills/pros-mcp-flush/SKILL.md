---
name: pros-mcp-flush
description: Remove Pros-managed MCP entries and their associated credentials from OpenCode and AnythingLLM on Windows to recreate a clean, not-yet-configured end-user state. Use when asked to flush, reset, wipe, clear, or clean the Pros MCP setup before repeated installation, onboarding, OAuth, or credential tests. Preserve Serena, Gitea, Codeberg, and every other non-Pros MCP entry.
---

# Pros MCP Flush

## Goal

Restore the Pros MCP setup boundary to a clean end-user state without uninstalling Pros or changing unrelated MCP servers.

## Workflow

1. Confirm that the request means **remove**, never install or synchronize.
2. Run a preview:

   ```powershell
   & ".\.agents\skills\pros-mcp-flush\scripts\flush-pros-mcp.ps1" -WhatIf
   ```

3. Inspect the reported client keys and credential targets. Never print secret values.
4. Run the flush:

   ```powershell
   & ".\.agents\skills\pros-mcp-flush\scripts\flush-pros-mcp.ps1" -Force
   ```

5. Verify the redacted result with the script output. If available, also run:

   ```powershell
   pros mcp status opencode
   pros mcp status anythingllm
   pros mcp hubspot credentials status
   pros mcp qnap token status
   pros integrations graph status
   opencode mcp list
   ```

6. Report remaining non-Pros MCPs explicitly. Treat them as preserved, not as incomplete cleanup.

## Scope

Remove:

- Pros-managed canonical and known legacy MCP keys from OpenCode and AnythingLLM.
- Local Pros MCPs for DOCX, Excel, PowerPoint, QNAP files, Microsoft Graph, HubSpot, and QNAP Assistant, including entries stored under custom aliases but using known Pros wrapper commands.
- `%USERPROFILE%\.config\pros\mcp\managed-state.json`.
- User and current-process `PROS_MICROSOFT_CLIENT_ID`.
- Credential targets for Pros HubSpot MCP, QNAP MCP Assistant, Microsoft Graph profiles, and their chunk records.

Preserve:

- Non-Pros MCP entries, including Serena, Gitea, and Codeberg.
- Pros installation files, CLI binaries, runtime files, and unrelated Pros authentication.
- Credentials outside the script's explicit Pros-MCP whitelist.

## Safety Rules

- Require `-Force` for changes; otherwise use `-WhatIf`.
- Do not run a general MCP sync before or after flushing because it can re-add entries from a host SSOT.
- Do not delete all Windows credentials matching `pros:*`; unrelated Pros auth may exist.
- Stop on malformed OpenCode or AnythingLLM config instead of rewriting or replacing it.
- Use `-HomePath`, `-OpenCodeConfig`, `-AnythingLlmConfig`, and `-ManagedStatePath` only for isolated tests or explicit alternate profiles.
- Use `-SkipCredentials` only for fixture tests, never to claim a real clean slate.

## Exit Criteria

- OpenCode and AnythingLLM contain none of the listed Pros MCP keys.
- OpenCode and AnythingLLM contain no entry whose command is a known Pros MCP wrapper.
- The Pros MCP managed-state file is absent.
- `PROS_MICROSOFT_CLIENT_ID` is absent at user scope.
- Whitelisted Pros MCP credentials are absent.
- Unrelated MCP entries remain byte-for-byte represented by the parsed configuration.
