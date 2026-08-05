# QA Progress - Docling Tool Skill

Status: Step 6 completed; Step 6.1 skipped

QA result: FAIL

Findings:
- HIGH: packages/pros-cli/scripts/prepare-tool-skills.js misses docling, so published CLI package would not include docling under tool-skills.
- MEDIUM: runtime/pros/.agents/skills/docling/scripts/docling_convert.py --dry-run can print --pdf-password.
- MEDIUM: tests use synthetic tool-skill sources and do not cover prepare/package pipeline.

Quality score: skipped because automated measurement was not active/configured for this workflow.