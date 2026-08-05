Status: done

Summary:
- README HubSpot snippet updated to use masked `Read-Host -MaskInput`, a `try/finally` cleanup block, and removal of the secret variables after piping to stdin.
- README Microsoft Graph local start command corrected to `mcp-microsoft-graph`.
- Tracker `docs/plans/work/026-pros-mcp-setup-repair.md` updated: Tasks 1-7 set to DONE and Done-When checklist checked off.

Verification:
- `oma docs verify --json` returned `scannedDocs: 1021`, `totalRefs: 5428`, `skippedCount: 203`, and 331 broken refs, all existing repo-wide drift outside this slice.
- `oma docs sync HEAD~1..HEAD --json` did not propose any further doc patch for this slice.
- Targeted grep checks confirmed the README anchors and tracker state.

Files changed:
- README.md
- docs/plans/work/026-pros-mcp-setup-repair.md
- .agents/results/result-docs-remediation-pros-mcp-setup-repair-20260707.md