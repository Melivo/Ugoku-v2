# PM Progress - Docling Tool Skill

Status: completed
Session: work-docling-tool-skill-20260704

PM validated plan 022 as implementation-ready.

Key decision: no file move required; runtime/pros/.agents/skills/docling remains the shared source, but classification changes from local runtime skill to GLOBAL_TOOL_SKILLS.

Critical path: remove docling from LOCAL_RUNTIME_SKILLS -> add to GLOBAL_TOOL_SKILLS -> update runtime projection assertions -> validate.

API contracts: not required; internal TS constants and packaging behavior only.