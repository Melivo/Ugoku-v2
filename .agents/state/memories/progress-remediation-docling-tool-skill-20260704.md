# Remediation Progress - Docling Tool Skill

Status: Step 7 attempt 1 completed

Root-cause fixes reported:
- packages/pros-cli/scripts/prepare-tool-skills.js includes docling in real packaging pipeline.
- prepare-tool-skills script refactored for regression testing.
- docling_convert.py dry-run redacts --pdf-password while real execution passes password to Docling.
- Regression tests added for prepare pipeline and docling dry-run/password behavior.

Next: re-run Step 5 monitoring and Step 6 QA review.