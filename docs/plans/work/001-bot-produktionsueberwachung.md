# Produktionsüberwachung für Ugoku

> Der Bot erkennt Funktionsstörungen, meldet sie in Discord und stellt sich kontrolliert innerhalb von fünf Minuten wieder her.

**Status**: Active — T1–T9 lokal erledigt; T10 bis zur echten Betriebsabnahme offen
**Created**: 2026-08-04
**Owner**: backend, tf-infra, qa, docs

## Goal
Slash-Commands und Audio-Funktionen sind nachweisbar verfügbar. Blockierte Ressourcen, ausgefallene Gateway-Verbindungen und hängende Event Loops werden erkannt, gemeldet und kontrolliert wiederhergestellt.

## Context
Am 2026-08-04 reagierte der laufende Bot nicht mehr auf Slash-Commands. Ursache waren unzureichend verwaltete Voice-, FFmpeg- und Librespot-Ressourcen. Ein erster Lifecycle-Fix ist produktiv ausgerollt; diese Arbeit ergänzt belastbare Überwachung und Abnahme.

## Constraints
- Betrieb auf `automation` als `ugoku.service`.
- Alarmierung erfolgt in einen konfigurierten Discord-Admin-Kanal.
- Zwei fehlgeschlagene Health-Checks lösen einen deduplizierten non-blocking Restart aus; ein gesunder post-READY-Pfad schließt die Recovery operational innerhalb von fünf Minuten nach Incident-Beginn ab. Die durable RECOVERY-Zustellung darf unabhängig pending und retryfähig bleiben.
- Audio-Proben dürfen aktive Nutzer-Queues nicht beeinträchtigen.

## Tasks

| # | Task | Agent | Priority | Status | Dependencies | Lokale Evidence |
|---|---|---|---|---|---|---|
| 1 | Gesundheitsmodell mit messbaren Grenzwerten definieren | backend | 1 | DONE | — | `config.py`, `bot/health/monitor.py`, `tests/test_health_monitor.py` |
| 2 | Internen Health-Check mit Diagnose und Exit-Codes implementieren | backend | 1 | DONE | 1 | `scripts/healthcheck.py`, `tests/test_healthcheck_cli.py` |
| 3 | Geschützten Discord-Admin-Health-Command implementieren | backend | 1 | DONE | 1, 2 | `commands/admin/health.py`, `tests/test_admin_health_command.py` |
| 4 | Kontrollierte Audio-Probe mit vollständigem Cleanup implementieren | backend | 2 | DONE | 1, 2 | `bot/health/audio_probe.py`, `bot/health/cleanup.py`, `tests/test_audio_probe.py` |
| 5 | systemd-Watchdog und Timer einrichten | tf-infra | 2 | DONE | 2 | `deploy/ugoku*.service`, `deploy/ugoku-health.timer`, `tests/test_systemd_units.py` |
| 6 | Discord-Alarmierung für Ausfall, Restart und Recovery einrichten | backend | 2 | DONE | 2, 5 | Durable Outbox und Incident-Tests in `tests/test_healthcheck_cli.py` |
| 7 | Shutdown-Lifecycle vollständig begrenzen und aufräumen | backend | 2 | DONE | 1 | `main.py`, `tests/test_shutdown_budget.py`, `tests/test_close_cleanup_disconnect.py` |
| 8 | Lifecycle-Regressionstests ergänzen | qa | 3 | DONE | 2, 4, 7 | Vollständige lokale Suite unter `tests/` inklusive Child-Reaping und SLA-Budget |
| 9 | Produktions-Runbook erstellen | docs | 3 | DONE | 5, 6, 8 | `docs/runbooks/bot-produktionsueberwachung.md` |
| 10 | Staging- und Produktionsabnahme mit Fehlerübungen durchführen | qa | 4 | TODO | 3, 4, 5, 6, 7, 8, 9 | Offen: leere Evidence-Felder in `docs/acceptance/001-bot-produktionsueberwachung.md` |

## Done When
- [x] Der Bot erkennt fehlende Gateway-Verbindung und einen blockierten Event Loop (lokale Code-/Test-Evidence).
- [x] Zwei Fehlversuche bewirken genau einen kontrollierten Restart; ein gesunder post-READY-Pfad schließt operational innerhalb des getesteten 295s-Gesamtbudgets ab.
- [x] OUTAGE/RESTART/RECOVERY werden durable geordnet; pending Ereignisse bleiben atomar retryfähig und blockieren weder Incident-Abschluss noch den nächsten Restart.
- [x] Slash- und Audio-Health-Checks sind automatisiert; N/A ist ausschließlich bei deaktiviertem Spotify zulässig.
- [x] Lifecycle-Integrationstests decken hängende Streams und Kindprozesse einschließlich Poll/Kill/Wait nach angeblich erfolgreichem Cleanup ab.
- [x] Das Runbook enthält Diagnose, Recovery und Eskalation.
- [ ] Echte Staging- und Production-Evidence für systemd, Discord-Zustellung, Fehlerübungen und Ende-zu-Ende-Zeiten liegt vor (T10).

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-04 | systemd-Timer statt externer Monitoring-Plattform | Keine neue Infrastruktur oder Credentials erforderlich. |
| 2026-08-04 | Zwei Fehlversuche vor Restart | Verhindert Restarts bei kurzen Discord- oder Spotify-Netzstörungen. |
| 2026-08-04 | Kontrollierte, kurze Audio-Probe | Prüft die kritische Kette ohne aktive Musik-Queues zu stören. |
| 2026-08-04 | Discord als Alarmkanal | Entspricht dem gewünschten Betriebsweg. |
| 2026-08-05 | Recovery-SLA endet beim operationalen Abschluss nach striktem post-READY-Healthcheck; RECOVERY wird zuvor durable eingereiht | Ein externer Webhook-Ausfall darf keinen aktiven Incident und damit den nächsten Restart blockieren; die Outbox bleibt geordnet retryfähig. |
| 2026-08-05 | Timer auf 110s verkürzt und Stop-Budget in die SLA aufgenommen | 225s Detection + 5s Trigger + 25s Stop + 5s RestartSec + 30s Boot/READY + 5s Recovery = 295s ≤300s. |

## Progress Notes

- [2026-08-04] Plan erstellt und durch den Nutzer freigegeben.
- [2026-08-05] T1–T9 anhand lokaler Implementierungs-, Unit- und Test-Evidence auf DONE gesetzt. T10 bleibt ausdrücklich offen; es wurden keine Staging-/Production-Operationen durchgeführt.
