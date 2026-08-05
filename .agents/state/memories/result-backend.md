## Status: completed

## Summary

- Sieben lokale HIGH-Befunde minimal behoben: leere ENV-Pfade, Spotify-Audio-N/A, vollständiges 295s-SLA-Budget, OnFailure/Restart-Ordering, nicht blockierende Recovery-Outbox, Child-Reaping sowie evidenzbasierter Planstatus.
- Re-Review im Änderungsscope: keine offenen CRITICAL/HIGH-Befunde. T10 bleibt absichtlich offen, weil echte Staging-/Production-Evidence aussteht.
- Keine Staging-/Production-Operationen ausgeführt.

## Files Changed

- `.env.template`, `config.py`
- `bot/health/audio_probe.py`, `bot/health/cleanup.py`
- `scripts/healthcheck.py`
- `deploy/ugoku-health.timer`, `deploy/ugoku-alert-onfailure.service`
- `tests/test_config_health_paths.py`, `tests/test_audio_probe.py`, `tests/test_healthcheck_cli.py`, `tests/test_systemd_units.py`
- `docs/plans/work/001-bot-produktionsueberwachung.md`
- `docs/runbooks/bot-produktionsueberwachung.md`
- `docs/acceptance/001-bot-produktionsueberwachung.md`
- `.agents/results/result-backend.md`
- `.agents/state/memories/progress-backend.md`, `.agents/state/memories/result-backend.md`

## Verification

- Vollständige Suite: 58 Tests bestanden.
- Compileall, Ruff E9/F, Dependency-Check und `git diff --check`: bestanden.
- `pip-audit`: keine bekannten Vulnerabilities.
- Bandit im geänderten Monitoring-Scope: 0 HIGH; der vollständige Repo-Lauf meldet nur zwei bestehende nicht-kryptografische MD5-Identifier außerhalb dieses Scopes.
- `visudo -cf`: parsed OK.
- `systemd-analyze verify`: keine Unit-Ordering-Zyklen; nur erwartete DrvFS-Moduswarnungen und auf dem lokalen Prüfhost fehlende Produktions-Exec-Pfade.
- Coverage konnte mangels installiertem `coverage`-Modul nicht frisch wiederholt werden; vorhandene lokale QA-Evidence dokumentiert 88% für den Vertrags-Scope.

## Acceptance Criteria Checklist

- [x] Leere ENV-Werte fallen auf `/run/ugoku`-Defaults zurück.
- [x] Audio N/A nur bei deaktiviertem Spotify; aktive fehlende/unlesbare Probe ist `AUDIO_NOT_READY`.
- [x] Timer/Restart/Stop/Boot/Recovery ergeben getestet 295s und damit garantiert höchstens 300s.
- [x] `Before=ugoku.service` ordnet den OnFailure-Hook ohne Requirement-Zyklus vor dem Restart.
- [x] Operationaler Recovery-Abschluss ist von Webhook-Zustellung entkoppelt; Outbox bleibt retryfähig und Folge-Incidents dürfen restarten.
- [x] Cleanup prüft Child-Prozesse mit Poll/Kill/Wait auch nach angeblichem Erfolg.
- [x] T1–T9 sind lokal evidenzbasiert DONE; T10 und echte Betriebs-Evidence bleiben offen dokumentiert.
- [x] Keine realen Staging-/Production-Operationen.
