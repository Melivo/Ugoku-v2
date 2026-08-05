## Status: completed

# QA SHIP Recheck — Session 20260713-173850

## Review Result: WARNING

**SHIP_GATE: HOLD — ein in-scope Dokumentationsbefund ist offen; danach technisch PASS, weiterhin vorbehaltlich der finalen Nutzerfreigabe.**

- Scope: ausschließlich Remediation des früheren SHIP-HOLD
- Commit: `f560528a59dc0611790733995c4bc06b16196199`
- CRITICAL: 0
- HIGH: 0
- MEDIUM: 1
- LOW: 0
- Produktivcode geändert: nein

## Summary

Der Work-Tracker ist in `docs/plans/work/030-ci-cache-backend-and-mise.md:5,27-41` korrekt auf **Completed**, Tasks 1–6 auf **DONE** und alle Done-When-Punkte auf erledigt gesetzt. Die technische Remediation ist belegt:

- `HEAD == main == origin/main == f560528a59dc0611790733995c4bc06b16196199`.
- Forgejo-Runs #217–#221 sind live `completed/success` auf Runner `automation-ci`.
- #217/#218 liefen auf dem vorherigen SHA `93cb78f` und belegen laut persistierten zeitnahen TF-/QA-Handoffs Cold Save bzw. Warm Restore nach Podman-/netavark-Bridge-Recovery.
- #219 (PR), #220 (main push) und #221 (main dispatch) liefen auf `f560528`; die Handoffs belegen PR-Isolation, Trusted Miss/Save und Trusted mise+npm Restore.
- Die Konfiguration implementiert die für act_runner v0.2.11 erforderliche Workflow-Isolation: PR-spezifische `npm-pr-<PR-Nr>-*`-Keys, `npm-trusted-*` für main/Release, mise-Cache in PRs aus und in trusted CI-/Release-Pfaden an.

Ein verbleibender Dokumentationsfehler verhindert jedoch die Bestätigung „keine neue in-scope Drift“: Die Abschlussnotiz bezeichnet 80 % als Coverage-„Baseline“, obwohl die unveränderte und vom Nutzer akzeptierte repositoryweite Baseline 71,39 % Lines beträgt. Die Coverage selbst ist ausdrücklich **keine zu behebende Produktabweichung**, sondern eine dokumentierte Scope-Ausnahme.

## Step 14 — Code Quality Review

**PASS mit akzeptierter Coverage-Ausnahme.**

Exact-Commit-Prüfung in einem LF-isolierten temporären Worktree:

- `npm ci`: PASS, 200 Pakete / 202 auditiert
- `npm audit --audit-level=low`: PASS, 0 Schwachstellen
- `npm run lint`: PASS, 68 Dateien
- `npm run typecheck`: PASS
- `npm run build`: PASS
- `npm test -- --run`: PASS, 27 Dateien / 224 bestanden / 1 übersprungen
- `npm run coverage`: 71,37 % Statements, 55,56 % Branches, 84,49 % Functions, **71,39 % Lines**

Bewertung: Die 71,39-%-Baseline ist unverändert, außerhalb des CI-Cache-Scopes und vom Nutzer ausdrücklich akzeptiert. Kein Finding und kein Remediation-Auftrag.

Hinweis: Der Root-Checkout reproduziert wegen Windows-CRLF-Materialisierung einen Biome-Formatfehler in `tests/release-workflow.test.ts`; derselbe Git-Blob besteht nach LF-treuer Materialisierung. Kein Source-Finding.

## Step 15 — UX / Operational Flow

**PASS.** Kein UI-/WCAG-Scope; der Operationspfad ist relevant.

- PR: `.gitea/workflows/ci.yaml:20,27-29` — mise aus, npm-PR-Namespace.
- Trusted main: mise an, npm Trusted-Namespace; #220/#221 erfolgreich.
- Release: `.gitea/workflows/release.yaml:21,27-30` — mise an, ausschließlich npm Trusted-Namespace.
- Cache-Ausfall: `continue-on-error: true` bleibt erhalten; `scripts/npm-ci-retry.sh`/`npm ci` bleibt Korrektheitspfad.
- Kein `node_modules`-Cache; Pfad ist `~/.npm`.

## Step 16 — Related Issues / Cascade Impact

**WARNING.**

- Commit-Diff `f560528^..f560528`: ausschließlich `.gitea/workflows/ci.yaml`, `.gitea/workflows/release.yaml`, `tests/release-workflow.test.ts`.
- `oma docs verify --json`: 1.114 Dokumente, 6.145 Referenzen, 344 bekannte repositoryweite Brüche; für `docs/plans/work/030-ci-cache-backend-and-mise.md` **0** gebrochene Referenzen.
- Inhaltliche Scope-Prüfung: Trackerstatus, Runs, Commit und Isolation korrekt; Coverage-Wortlaut an Zeile 55 inkonsistent (siehe MEDIUM).

## Step 17 — Deployment Readiness

**PASS_WITH_RISKS.**

- `HEAD`, `main`, `origin/main`: exakt `f560528`.
- Runs #217–#221: live `completed/success`; Jobs 323–327 auf `automation-ci`.
- Security: Audit 0; keine neuen Secrets; Release-Publishing/Trigger außerhalb des Commit-Diffs.
- Rollback: Revert von `f560528`; Cache bleibt Performance-Optimierung und `npm ci` bleibt funktionaler Pfad.
- Keine Migration, keine Produktivcode-Änderung, kein neuer Release-Tag.

## Findings

### CRITICAL
- Keine.

### HIGH
- Keine.

### MEDIUM
- `docs/plans/work/030-ci-cache-backend-and-mise.md:55` — Die Abschlussnotiz nennt eine „unveraenderte 80%-Gesamtabdeckungs-Baseline“. Tatsächlich beträgt die unveränderte, vom Nutzer akzeptierte repositoryweite Baseline 71,39 % Lines; 80 % ist nur die formale SHIP-Schwelle. Damit ist die Scope-Ausnahme im Tracker sachlich missverständlich dokumentiert und die Anforderung „keine neue in-scope Dokumentationsdrift“ noch nicht erfüllt. **Fix:** Satz ersetzen durch:
  ```md
  Die unveraenderte repositoryweite Coverage-Baseline von 71,39 % Lines liegt unter der formalen 80-%-SHIP-Schwelle und bleibt als vom Nutzer genehmigte, non-blocking Ausnahme ausserhalb des CI-Cache-Scopes.
  ```

### LOW
- Keine.

## SHIP_GATE Checklist

- [x] Exact-Commit-Audit, Lint, Typecheck, Build und Tests bestanden.
- [x] Coverage 71,39 % reproduziert und als explizit akzeptierte, unveränderte Scope-Ausnahme bewertet.
- [x] Tracker Status `Completed`, Tasks 1–6 `DONE`, Done-When vollständig.
- [x] Runs #217–#221 live als erfolgreich belegt; Cache-Details durch persistierte zeitnahe Handoffs belegt.
- [x] Commit `f560528` auf `HEAD`, `main` und `origin/main`.
- [x] act_runner-v0.2.11-Isolationsstrategie technisch korrekt und im Tracker beschrieben.
- [ ] Keine neue in-scope Dokumentationsdrift — Coverage-Wortlaut in Zeile 55 offen.
- [x] Keine Produktivcode-Änderung durch diesen Recheck.
- [ ] Finale Nutzerfreigabe.

**SHIP_GATE: HOLD.** Nach der reinen Textkorrektur in Zeile 55 wäre der technische Gate-Status **PASS, vorbehaltlich der finalen Nutzerfreigabe**.

## Rest-Risiken / Evidenzgrenzen

1. Private Forgejo-Step-Logs sind via PAT weiterhin wegen `rasterstate/fj#103` nicht abrufbar; Actions API liefert `steps: null`. Live bestätigt sind Run-/Jobstatus, SHA und Runner. Cache-Hit/Miss-Keydetails stammen aus den persistierten zeitnahen TF-/QA-Handoffs derselben Session.
2. #217/#218 validieren den reparierten Backendpfad auf dem Vorläufer-SHA `93cb78f`; #219–#221 validieren die neue Isolation auf `f560528`.
3. Kein realer `pros-v*`-Release wurde ausgelöst. Der Releasepfad ist statisch und durch Tests/Trusted-Konfiguration validiert; den ersten realen Release beobachten.
4. Der Root-Arbeitsbaum enthält fremde Änderungen. Release/Tag nur aus `f560528` bzw. sauberem Checkout erzeugen.
5. Repositoryweit bestehen 344 bekannte Docs-Verify-Befunde; keiner betrifft den Scope-Tracker. Sie sind nicht durch diese Remediation entstanden.

## Files Changed

- Serena Memory `progress-qa-agent-ship-recheck-20260713-173850`
- Serena Memory `result-qa-agent-ship-recheck-20260713-173850`
- Serena Memory `session-ultrawork` (Abschluss-Append)

Keine Produktivcode-, Workflow- oder Dokumentationsdatei geändert.

## Acceptance Criteria

- [x] Ausschließlich SHIP-HOLD-Remediation geprüft.
- [x] Tracker Completed/DONE verifiziert.
- [x] Runs #217–#221 und Commit `f560528` verifiziert.
- [x] act_runner-Isolationsstrategie verifiziert.
- [x] Coverage 71,39 % als akzeptierte Ausnahme, nicht als Bug, bewertet.
- [x] Neue in-scope Drift geprüft und ein verifizierter Wortlautfehler gemeldet.
- [x] Steps 14–17, SHIP_GATE und Rest-Risiken dokumentiert.
- [x] Keine Produktivcode-Änderung vorgenommen.
