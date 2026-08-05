# Abnahmeprotokoll: Ugoku-Produktionsüberwachung

Dieses Protokoll ist eine Vorlage und markiert T10 ausdrücklich als **OFFEN**. T1–T9 besitzen lokale Code-/Test-Evidence; es wurde jedoch keine Staging- oder Produktionsabnahme ausgeführt. Echte Nachweise dürfen erst nach Durchführung durch die verantwortlichen Personen eingetragen werden.

- Runbook: `docs/runbooks/bot-produktionsueberwachung.md`
- Planquelle: `.agents/results/plan-20260805-000000.json`
- CCR-Remediation: `.agents/results/plan-20260805-ccr-step7-remediation.json`
- Units: `deploy/ugoku.service`, `deploy/ugoku-health.service`, `deploy/ugoku-health.timer`, `deploy/ugoku-alert-onfailure.service`
- Healthcheck: `scripts/healthcheck.py`

## Deploy-Nachweise

| Feld | Staging | Production |
|---|---|---|
| Host |  |  |
| Git-Revision |  |  |
| Artefakt-/Release-ID |  |  |
| Deploy-Start UTC |  |  |
| Deploy-Ende UTC |  |  |
| Ausführende Person |  |  |
| `systemd-analyze verify deploy/*.service deploy/*.timer` Ergebnis |  |  |
| `visudo -cf deploy/ugoku-restart.sudoers` Ergebnis |  |  |
| `systemctl status ugoku.service ugoku-health.timer` Nachweis |  |  |
| Test-/Coverage-Nachweis T8 (`>=80%`) |  |  |

## Mechanische Fehlerübungen

Alle Übungen erfassen `incident_id`, `fault_started_at_wall`, `ended_at_wall`, Exit-Code, Journal-Auszug und Discord-Alarmnachweis. Produktionsübungen nur nach Freigabe im Wartungsfenster durchführen.

### A1 Gateway-/Readiness-Verlust über Timer-Pfad

Ziel: Zwei fehlerhafte Proben führen zu genau einem Restart und bei gesundem post-READY-State zum operationalen Recovery-Abschluss mit zuvor durable eingereihtem RECOVERY innerhalb von 300s. Die Webhook-Zustellung kann unabhängig pending bleiben.

Mechanik:

```sh
/home/leadt3ch/.local/bin/uv run --python /home/leadt3ch/ugoku/venv/bin/python scripts/healthcheck.py --json
systemctl list-timers ugoku-health.timer
journalctl -u ugoku-health.service -u ugoku.service --since "10 minutes ago" --no-pager
```

Erwartung: Exit 3 bei `GATEWAY_DOWN` oder Exit 7/8 bei Slash-/Audio-Readiness nach Grace; nach zwei Strikes genau ein `RESTART`; `RECOVERY` wird vor dem operationalen Abschluss durable eingereiht. Zeitgrenze: `fault_started_at_wall`→operationales Recovery-Ende ≤300s; Zustellzeit separat erfassen.

| Nachweisfeld | Staging | Production |
|---|---|---|
| Simulationsmethode/Freigabe |  |  |
| Start UTC |  |  |
| Exit-Code |  |  |
| fail.count-Sequenz |  |  |
| incident_id |  |  |
| Restart-Anzahl |  |  |
| RECOVERY UTC |  |  |
| Dauer Sekunden |  |  |
| PASS/FAIL |  |  |

### A2 Blockierter Event Loop über Watchdog-Pfad

Ziel: systemd-Watchdog erkennt den hängenden Loop; die `Before=ugoku.service`-Relation des `OnFailure`-Hooks erfasst die ursprüngliche `fault_boot_id`; `ExecStartPost --recover` schließt den Incident nach strikt gesundem State und durable eingereihtem RECOVERY, ohne auf Zustellung zu warten.

Mechanik:

```sh
systemctl show ugoku.service -p WatchdogUSec -p Type -p Restart -p RestartUSec
journalctl -u ugoku.service -u ugoku-alert-onfailure.service --since "15 minutes ago" --no-pager
cat /run/ugoku/incident.json
cat /run/ugoku/alert-outbox.json
```

Erwartung: Watchdog-Pfad unter 300s; `OUTAGE`, `RESTART` und `RECOVERY` tragen dieselbe `incident_id`; Delivery-Status wird separat belegt und darf zunächst pending sein. Kein Bot-Loop-Webhook und kein RECOVERY bei nur Grace-bedingtem Exit 0.

| Nachweisfeld | Staging | Production |
|---|---|---|
| Loop-Block-Simulation/Freigabe |  |  |
| Watchdog-Kill UTC |  |  |
| OnFailure-OUTAGE UTC |  |  |
| OnFailure-RESTART UTC |  |  |
| READY/RECOVERY UTC |  |  |
| incident_id |  |  |
| Dauer Sekunden |  |  |
| PASS/FAIL |  |  |

### A3 RESOURCE_BLOCKED

Ziel: Voice-/FFmpeg-/Librespot-Blockaden werden als Exit 6 erkannt, alarmiert und nach Recovery aufgehoben.

Mechanik:

```sh
/home/leadt3ch/.local/bin/uv run --python /home/leadt3ch/ugoku/venv/bin/python scripts/healthcheck.py --json
journalctl -u ugoku-health.service -u ugoku.service --since "15 minutes ago" --no-pager
cat /run/ugoku/health.json
```

Erwartung: `resource_blocked.blocked=true`, `reason` ist `voice`, `ffmpeg` oder `librespot`; Exit 6; nach Recovery Exit 0.

| Nachweisfeld | Staging | Production |
|---|---|---|
| Blockade-Prädikat |  |  |
| Exit-Code vorher/nachher |  |  |
| Alarmereignisse |  |  |
| incident_id |  |  |
| Dauer Sekunden |  |  |
| PASS/FAIL |  |  |

### A4 Slash-/Audio-Readiness und `/health`

Ziel: Exit 7/8 sind negativ verbindlich; bei aktivem Spotify erfordert Exit 0 `slash_ready=true` und `audio_ready=true`. `audio_ready=null` ist ausschließlich bei deaktiviertem Spotify N/A. `/health` ist nur für Admin/Owner sichtbar.

Mechanik:

```sh
/home/leadt3ch/.local/bin/uv run --python /home/leadt3ch/ugoku/venv/bin/python scripts/healthcheck.py --json
```

Zusätzlich Discord `/health` ohne Audio und mit `audio=true` durch berechtigte Person ausführen; normaler Guild-Member muss abgewiesen werden.

| Nachweisfeld | Staging | Production |
|---|---|---|
| `slash_ready` |  |  |
| `audio_ready` |  |  |
| `/health` Admin/Owner PASS |  |  |
| `/health` normaler Member abgewiesen |  |  |
| Audio-Probe Dauer Sekunden |  |  |
| Queue unbeeinträchtigt |  |  |
| PASS/FAIL |  |  |

### A5 Shutdown und Rollback-Bereitschaft

Ziel: Shutdown endet innerhalb von 20s ohne verwaiste Kindprozesse; Rollback-Schritte aus dem Runbook sind nachvollziehbar.

Mechanik:

```sh
journalctl -u ugoku.service --since "15 minutes ago" --no-pager
systemctl status ugoku.service ugoku-health.timer
```

Erwartung: keine SIGKILL-bedingten Reste nach `TimeoutStopSec=25`; T8-Tests `close/cleanup/disconnect` sowie Poll/Kill/Wait des Child-Prozesses grün; Rollback-Entscheidung dokumentiert, aber nicht ohne Freigabe ausgeführt.

| Nachweisfeld | Staging | Production |
|---|---|---|
| Shutdown-Dauer Sekunden |  |  |
| Verwaiste FFmpeg/Librespot-Prozesse |  |  |
| T8-Testnachweis |  |  |
| Rollback-Freigabe erforderlich? |  |  |
| PASS/FAIL |  |  |

## Abschlussentscheidung

**Aktueller Status: T10 offen.** Die folgenden Felder benötigen echte Staging-/Production-Evidence und bleiben bis dahin leer; lokale Tests ersetzen diese Betriebsnachweise nicht.

| Kriterium | Staging | Production |
|---|---|---|
| Alle Fehlerübungen PASS |  |  |
| SLA ≤300s nachgewiesen |  |  |
| Discord OUTAGE/RESTART/RECOVERY mit gleicher `incident_id` nachgewiesen |  |  |
| Outbox-Retry und ausschließlich zugestellte Events als `delivered=true` nachgewiesen |  |  |
| Keine Produktionseingriffe außerhalb Freigabe |  |  |
| Abnahme erteilt durch / UTC |  |  |
