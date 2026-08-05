# Work Result - Docling Global Tool Skill

Status: completed

Implemented:
- docling is no longer a local pros init runtime skill.
- docling is now part of GLOBAL_TOOL_SKILLS and installed/updated via pros tools/pros tools update.
- Real packaging pipeline includes docling in packages/pros-cli/tool-skills.
- Runtime projection tests ensure global tool skills are excluded from case-folder runtime output.
- CLI/tool-skill tests verify docling global installation.
- Docling dry-run redacts --pdf-password while real execution still passes the password to Docling.
- Runtime manifest documents docling as global Tool-Skill.
- Plan 022 marked Completed.

QA:
- Initial QA found HIGH packaging gap and MEDIUM dry-run/test gaps.
- Root-cause remediation completed.
- QA re-review PASS with no open findings.

Validation reported by agents:
- npm --workspace @pro-select/pros-cli test
- npm --workspace @pro-select/pros-cli run lint
- npm --workspace @pro-select/pros-cli run typecheck
- node scripts/validate-runtime-files.js
- npm --workspace @pro-select/pros-cli pack --dry-run --json includes tool-skills/docling/*