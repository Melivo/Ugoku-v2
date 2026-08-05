CCR Step 2 — Completeness Review ONLY.

You are a FRESH, CONTEXT-ISOLATED reviewer. Assume NO prior context about this project or any conversation. Do NOT converse. You are READ-ONLY: modify NO application code. Read the artifacts fresh, evaluate against the single review guide below, then write exactly one structured verdict to the memory path given and stop.

INPUTS (read these fresh, by path):
1. Plan artifact: .agents/results/plan-20260805-000000.json
2. Source requirements (the approved plan you must map against): docs/plans/work/001-bot-produktionsueberwachung.md
3. Codebase context (read only as needed to judge feasibility of coverage): main.py, deploy/ugoku.service, bot/vocal/server_session.py, config.py

YOUR SINGLE REVIEW GUIDE — Completeness Review (Step 2):
- Question: "Is anything missing?"
- Check: Map EVERY requirement and Done-When criterion to plan items (target 1:1 coverage).
- Pass Condition: All requirements from the source plan are reflected in the plan artifact.

Specifically verify coverage for each of these source requirements / Done-When items:
- Bot erkennt fehlende Gateway-Verbindung.
- Bot erkennt einen blockierten Event Loop.
- Zwei Fehlversuche bewirken genau einen kontrollierten Restart innerhalb von 5 Minuten.
- Discord meldet Ausfall, Restart und erfolgreiche Wiederherstellung im Admin-Kanal.
- Slash- und Audio-Health-Checks sind automatisiert und nachweisbar erfolgreich.
- Lifecycle-Integrationstests decken haengende Streams und Kindprozesse ab.
- Runbook enthaelt Diagnose, Recovery und Eskalation.
- Constraints: Betrieb als ugoku.service auf 'automation'; Alarmierung in Discord-Admin-Kanal; Audio-Proben duerfen aktive Nutzer-Queues nicht beeintraechtigen.

For EACH item, identify the covering task id(s), contract section(s), and acceptance criterion(ies) in the plan artifact. Flag any item with NO covering task/contract/acceptance criterion as a gap.

OUT OF SCOPE for this review (other reviewers own these): implementation correctness, code style/consistency, and over-engineering/simplicity. Evaluate ONLY completeness coverage.

OUTPUT — write your structured verdict as a Markdown file at EXACTLY this path:
.agents/state/memories/review-plan-step2-completeness.md

Use this format:
```
review: Completeness (Step 2)
verdict: PASS | FAIL
coverage_map:
  - requirement: <short name>
    source: <section of docs/plans/work/001-...>
    covered_by: <task ids / contract keys / acceptance criteria ids>  OR  UNCOVERED
    note: <one line>
findings:
  - severity: CRITICAL|HIGH|MEDIUM|LOW
    requirement: <which requirement>
    gap: <what is missing or unmapped>
    fix: <concrete suggestion>
evidence: <list the artifact paths you actually read>
summary: <2-3 sentences>
```

After writing the file, print the `verdict:` line and stop. Do not modify any other file.
