## Status: completed

## Review Result: FAIL

### Summary

Frischer, zielgerichteter Review der letzten Startbudget-, Dependency- und Planstatus-Korrekturen sowie CRITICAL/HIGH-Sichtung des gesamten Monitoring-Diffs. Zwei voneinander unabhängige HIGH-Deploy-Blocker bleiben in `deploy/ugoku.service`; keine CRITICAL-Befunde. Dependency-Constraint und Planstatus sind konsistent.

### CRITICAL

- Keine.

### HIGH

- `deploy/ugoku.service:15` — `uv run` bleibt unter Unix als systemd-Mainprozess aktiv und wartet auf einen gestarteten Child-Prozess. `READY=1` und `WATCHDOG=1` werden jedoch vom Python-Child in `bot/health/monitor.py:69` bzw. `bot/health/monitor.py:112` gesendet. Bei `Type=notify` gilt ohne explizites `NotifyAccess=` effektiv `main`; systemd ignoriert damit die Child-Benachrichtigungen. Ergebnis: kein erfolgreicher READY-Übergang, Start-Timeout/Restart-Loop und wirkungsloser Watchdog. Verifiziert gegen uv `run_to_completion(Child)` und systemd `sd_notify`/`Type=notify`-Semantik. — Remediation:

  ```ini
  [Service]
  Type=notify
  ExecStart=/home/leadt3ch/ugoku/venv/bin/python /home/leadt3ch/ugoku/main.py
  ExecStartPost=-/home/leadt3ch/ugoku/venv/bin/python /home/leadt3ch/ugoku/scripts/healthcheck.py --recover
  ```

  Falls der uv-Wrapper zwingend bleiben muss, mindestens `NotifyAccess=all` setzen und den Child-Notify-Pfad in einem echten systemd-Integrationstest belegen.

- `deploy/ugoku.service:9` — `TimeoutStartSec=30s` begrenzt die vollständige Unit-Aktivierung einschließlich des nach `READY=1` ausgeführten `ExecStartPost` aus Zeile 16. Gleichzeitig darf die In-Process-Initialisierung laut `config.py:86` selbst 30s dauern und die Recovery-Verarbeitung besitzt laut `config.py:87` weitere 5s. Der behauptete getrennte 30s+5s-Vertrag kann daher nicht eingehalten werden; nahe am Bootlimit wird der Recovery-Hook vom Start-Timeout abgeschnitten und die Unit kann trotz READY scheitern. `tests/test_systemd_units.py:25-26` und `tests/test_systemd_units.py:120-135` schreiben die fehlerhafte Gleichsetzung fest, statt das kombinierte Budget zu prüfen. — Remediation:

  ```ini
  [Service]
  TimeoutStartSec=35s
  ```

  ```python
  # tests/test_systemd_units.py
  unit_start_budget = (
      config.HEALTH_SLA_BOOT_READY_S
      + config.HEALTH_SLA_RECOVERY_ALERT_S
  )
  assert unit_start_budget == 35
  assert "TimeoutStartSec=35s" in service
  ```

### MEDIUM

- Keine neuen verifizierten MEDIUM-Befunde im angeforderten Korrektur-Slice.

### LOW

- Keine neuen verifizierten LOW-Befunde im angeforderten Korrektur-Slice.

## Evidence

- Tests: `uv run --with pytest --with-requirements requirements.txt python -m pytest -q` → **63 passed, 25 subtests passed**.
- Compile: `python -m compileall -q bot commands scripts config.py main.py` → bestanden.
- Dependency-Security: `uvx pip-audit -r requirements.txt` → **keine bekannten Schwachstellen**.
- SAST: Bandit → **0 HIGH**, 1 MEDIUM (`urlopen` mit operator-konfigurierter Webhook-URL; kein verifizierter Angriffsweg), 3 LOW.
- Dependency-Auflösung: Linux/Python-3.12-Compile mit `deploy/constraints-linux-legacy-cpu.txt` löst reproduzierbar **`numpy==2.1.3`** auf; Constraint ist in README, Unit-Kommentar und Runbook vor Aktivierung dokumentiert.
- Lint: Ruff meldet 29 nicht-blockierende Qualitätsbefunde; Typecheck (Pyright) 19 Befunde, überwiegend dynamische py-cord-Attribute. Diese ändern die obige CRITICAL/HIGH-Klassifikation nicht.
- Deploy-Parser: `systemd-analyze verify` unter WSL/systemd 259 fand keinen Unit-Zyklus; die Prüfung konnte die produktiven absoluten `/home/leadt3ch/...`-Executables erwartungsgemäß nicht auf dem Prüfhost auflösen.
- Planstatus: `docs/plans/work/001-bot-produktionsueberwachung.md:5,34,43` und `.agents/results/plan-20260805-000000.json:6,9` sind konsistent: Implementierung lokal erfolgt, Gesamtplan **ACTIVE**, T10 ohne echte Betriebsabnahme offen. Remediation-Plan 002 ist konsistent **COMPLETED**.
- Accessibility: nicht anwendbar; der Diff enthält keine visuelle Web-/GUI-Oberfläche.
- Referenzen: systemd `systemd.service` dokumentiert, dass `ExecStartPost` Teil der Aktivierung ist; systemd `sd_notify` verlangt passendes `NotifyAccess`; uv `crates/uv/src/child.rs` wartet auf einen gestarteten Child-Prozess.

## Files Changed

- `.agents/results/result-qa.md` — QA-Artefakt.
- `.agents/state/memories/result-qa.md` — Orchestrator-/Memory-Handoff.
- `.agents/state/memories/progress-qa.md` — Fortschrittsstatus.
- Keine Quell-, Deploy-, Dokumentations- oder Testdatei geändert.

## Acceptance Criteria Checklist

- [x] Letzte Startbudget-Korrektur geprüft.
- [x] Dependency-Constraint und Auflösung geprüft.
- [x] Planstatus in Markdown und maschinenlesbarem Plan geprüft.
- [x] Gesamter Monitoring-Diff auf neue CRITICAL/HIGH-Befunde gesichtet.
- [x] Deploy, Dokumentation und Tests gelesen.
- [x] Automatisierte Tests, Compile, Audit, SAST, Lint und Typecheck ausgeführt.
- [x] Jeder Befund besitzt `file:line`, Beschreibung und Remediation-Code.
- [x] Keine Source-Code-Änderungen vorgenommen.
