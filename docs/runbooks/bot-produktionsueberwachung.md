# Produktions-Runbook: Ugoku-Bot-Überwachung

Dieses Runbook beschreibt die dokumentarische Betriebsführung für `ugoku.service`. Es führt keine Produktionsaktion aus; alle Befehle sind als geprüfte Referenz oder als durch einen Incident-Owner auszuführende Schritte zu verstehen.

## Geltungsbereich und Ownership

- Bot-Prozess: schreibt ausschließlich die Runtime-Datei /run/ugoku/health.json und sendet `READY=1`/`WATCHDOG=1` über den zentralen stdlib-Notifier im HealthMonitor.
- Externer Incident-Owner: `scripts/healthcheck.py` liest `health.json` und schreibt atomar die Runtime-Dateien `/run/ugoku/incident.json`, `/run/ugoku/fail.count` sowie die persistente Retry-Outbox `/run/ugoku/alert-outbox.json`.
- systemd-Units: `deploy/ugoku.service`, `deploy/ugoku-health.service`, `deploy/ugoku-health.timer`, `deploy/ugoku-alert-onfailure.service`.
- Restart-Recht: nur `deploy/ugoku-restart.sudoers` mit exakt `leadt3ch ALL=(root) NOPASSWD: /bin/systemctl --no-block restart ugoku.service`.

## Architektur und Alarmsemantik

| Fehlerklasse | Erkennung | Recovery-Pfad | Alarmereignisse |
|---|---|---|---|
| Blockierter Event Loop | `Type=notify` + `WatchdogSec=60` in `ugoku.service`; der Bot kann keinen `WATCHDOG=1` mehr senden. | systemd beendet/restartet `ugoku.service`; `OnFailure=ugoku-alert-onfailure.service`; dessen reine `Before=ugoku.service`-Ordnung erfasst die ursprüngliche `fault_boot_id` vor dem Neustart, ohne eine Requirement-Abhängigkeit oder einen Zyklus. Danach prüft `ExecStartPost=-... scripts/healthcheck.py --recover` den frischen Health-State strikt. | `OUTAGE` und `RESTART` über `--on-failure`, `RECOVERY` nach strikt gesundem post-READY-State. |
| Gateway-/Readiness-Fehler | `ugoku-health.timer` ruft alle 110s `scripts/healthcheck.py` auf. | Nach `HEALTH_FAILURE_THRESHOLD=2` löst der externe Check genau einen `sudo -n /bin/systemctl --no-block restart ugoku.service` aus. | `OUTAGE`, `RESTART`, danach `RECOVERY`, jeweils mit gleicher `incident_id`. |
| `RESOURCE_BLOCKED` | `health.json.resource_blocked.blocked == true`, Exit 6. Gründe: `voice`, `ffmpeg`, `librespot`. | Timer-Pfad mit 2-Strike und begrenztem Restart. | `OUTAGE`/`RESTART`/`RECOVERY`, keine Bot-Loop-Alarmierung. |

Exit-Codes von `scripts/healthcheck.py`: 0 `OK`, 2 `STALE`, 3 `GATEWAY_DOWN`, 4 `SPOTIFY_DOWN`, 5 `EVENT_LOOP_LAG`, 6 `RESOURCE_BLOCKED`, 7 `SLASH_NOT_READY`, 8 `AUDIO_NOT_READY`.

Alle drei Alarmtypen werden vor dem Versand dedupliziert in `alert-outbox.json` geschrieben. Ein Webhook-Fehler lässt das Ereignis pending; spätere Healthcheck-/Hook-Läufe liefern in der Reihenfolge OUTAGE → RESTART → RECOVERY erneut aus. Sobald der neue Boot strikt gesund ist und RECOVERY durable eingereiht wurde, wird der Incident operational beendet. Die Zustellung bleibt unabhängig retryfähig; ein pending RECOVERY blockiert daher keinen neuen Incident und keinen erneuten Restart.

## Installationsreferenz

## Deployment

Der Produktionshost ist ueber Tailscale SSH als `leadt3ch@automation`
erreichbar. Fuer ein reguläres Deployment den gepushten Branch
fast-forward aktualisieren, die Abhaengigkeiten mit dem Legacy-CPU-Constraint
pruefen und den Dienst neu starten:

```sh
ssh leadt3ch@automation
cd /home/leadt3ch/ugoku
git pull --ff-only origin fix/spotify-playlist-oauth
/home/leadt3ch/.local/bin/uv pip install \
  --python /home/leadt3ch/ugoku/venv/bin/python \
  -r requirements.txt \
  -c deploy/constraints-linux-legacy-cpu.txt
/home/leadt3ch/ugoku/venv/bin/python -c 'import numpy; assert numpy.__version__ == "2.1.3"'
sudo /bin/systemctl restart ugoku.service
/home/leadt3ch/.local/bin/uv run \
  --python /home/leadt3ch/ugoku/venv/bin/python \
  scripts/healthcheck.py --json
```

Wenn der erste Start an einer voruebergehend abgelehnten Librespot-Verbindung
scheitert, den systemd-Retry abwarten und den Healthcheck erneut ausfuehren.

Nur im geplanten Wartungsfenster und mit Root-Rechten ausführen:

```sh
/home/leadt3ch/.local/bin/uv pip install \
  --python /home/leadt3ch/ugoku/venv/bin/python \
  -r requirements.txt \
  -c deploy/constraints-linux-legacy-cpu.txt
/home/leadt3ch/ugoku/venv/bin/python -c \
  "import numpy; assert numpy.__version__ == '2.1.3'"
sudo install -o root -g root -m 0644 deploy/*.service deploy/*.timer /etc/systemd/system/
sudo visudo -cf deploy/ugoku-restart.sudoers
sudo install -o root -g root -m 0440 deploy/ugoku-restart.sudoers /etc/sudoers.d/ugoku-restart
sudo systemctl daemon-reload
sudo systemctl enable --now ugoku.service ugoku-health.timer
sudo chmod 0600 /home/leadt3ch/ugoku/.env /home/leadt3ch/ugoku/credentials.json /home/leadt3ch/ugoku/.spotify_cache
```

Der Constraint ist fuer den produktiven Legacy-x86-Host verbindlich: NumPy 2.2+
benoetigt dort nicht verfuegbare x86-64-v2-Instruktionen. Die Versionspruefung
muss deshalb vor Unit-Installation und Aktivierung erfolgreich sein.

`ugoku-alert-onfailure.service` wird nicht enabled; die Unit wird ausschließlich über `OnFailure=ugoku-alert-onfailure.service` aufgerufen. `Before=ugoku.service` ist nur eine Ordnungsrelation und erzeugt bewusst weder `Requires=` noch `After=ugoku.service`; dadurch entsteht kein systemd-Zyklus.

## Diagnoseablauf

1. Unit- und Timer-Status prüfen:

   ```sh
   systemctl status ugoku.service ugoku-health.timer ugoku-health.service ugoku-alert-onfailure.service
   systemctl list-timers ugoku-health.timer
   ```

2. Journale zeitlich korrelieren:

   ```sh
   journalctl -u ugoku.service -u ugoku-health.service -u ugoku-alert-onfailure.service --since "30 minutes ago" --no-pager
   ```

3. Runtime-State lesen:

   ```sh
   cat /run/ugoku/health.json
   cat /run/ugoku/incident.json
   cat /run/ugoku/fail.count
   cat /run/ugoku/alert-outbox.json
   ```

4. Nur diagnostisch ohne Nebenwirkungen prüfen:

   ```sh
   /home/leadt3ch/.local/bin/uv run --python /home/leadt3ch/ugoku/venv/bin/python scripts/healthcheck.py --json
   ```

5. Admin-Sicht prüfen: Discord `/health` nur als Guild-Administrator, Guild-Owner oder User aus `UGOKU_ADMIN_OWNER_IDS` ausführen. Mit `audio=true` gilt zusätzlich das Audio-Probe-Timeout.

## Sichere Recovery

- Bevorzugt: Timer-/Watchdog-Pfade automatisch arbeiten lassen und `incident_id` in `incident.json` sowie im Admin-Kanal vergleichen.
- Manueller Restart nur durch Incident-Owner und nur mit dem begrenzten Kommando:

  ```sh
  sudo -n /bin/systemctl --no-block restart ugoku.service
  ```

- Recovery-Hook manuell nur zur Diagnose/Idempotenzprüfung verwenden, nicht als Erfolg behaupten:

  ```sh
   /home/leadt3ch/.local/bin/uv run --python /home/leadt3ch/ugoku/venv/bin/python scripts/healthcheck.py --recover
   ```

- Ein Ergebnis `RECOVERED` bestätigt den operationalen Abschluss und die durable RECOVERY-Einreihung, nicht zwingend die Discord-Zustellung. Pending Events in `alert-outbox.json` weiter retryen lassen und niemals manuell als geliefert markieren.

## Rollback

1. Wenn die neuen Units eine Regression verursachen, Timer stoppen:
   `sudo systemctl disable --now ugoku-health.timer`.
2. Vorherige bekannte `ugoku.service` aus Deployment-Artefakten wieder installieren und `sudo systemctl daemon-reload` ausführen.
3. Eng begrenztes sudoers-Recht nur entfernen, wenn der externe Healthcheck nicht mehr produktiv verwendet wird: `sudo rm /etc/sudoers.d/ugoku-restart`.
4. Danach `systemctl status ugoku.service` und `journalctl -u ugoku.service --since "10 minutes ago" --no-pager` prüfen.

## Eskalation

- SLA-Gefahr: `fault_started_at_wall` bis `RECOVERY` nähert sich 300s oder überschreitet es.
- Restart-Schleife: mehrere neue `incident_id` in kurzer Folge.
- Alarmkanal defekt: `alert-outbox.json` enthält pending `OUTAGE`/`RESTART`/`RECOVERY`; Zustellung reparieren, die Outbox nicht manuell als geliefert markieren.
- Sicherheitsproblem: sudoers-Inhalt weicht von exakt einem Restart-Kommando ab.

## SLA-Math

Gesunder Timer-Pfad: Detection ≤225s (zwei Intervalle à 110s plus je 2s `AccuracySec` und 1s Reserve), non-blocking RestartTrigger ≤5s, Stop ≤25s, RestartSec ≤5s, Boot→READY ≤30s und Recovery-Verarbeitung ≤5s. Die vollständige konservative Rechnung lautet `225 + 5 + 25 + 5 + 30 + 5 = 295s` und garantiert damit ≤300s. Das In-Process-Limit erzwingt das 30s-Boot→READY-Budget; `TimeoutStartSec=35s` umfasst zusätzlich den auf 5s begrenzten `ExecStartPost`-Recovery-Check als Teil der vollständigen Unit-Aktivierung. Spotify wird dabei nur einmal initialisiert, und ein Fehler wird an systemd propagiert statt intern unbegrenzt wiederholt. Der Hook läuft erst nach `Type=notify`-READY; `NotifyAccess=all` erlaubt dabei die `READY=1`-/`WATCHDOG=1`-Nachrichten des von `uv` gestarteten Python-Childs. Der Recovery-Check akzeptiert weder Grace-False-Positives noch alte Snapshots. Der Watchdog-Pfad bleibt mit WatchdogSec=60 plus Stop/Restart/Boot/Recovery ebenfalls unter 300s. Ist Discord nicht erreichbar, ist der Incident nach durable eingereihtem RECOVERY operational beendet, während die externe Zustellung korrekt pending und retryfähig bleibt.

## Evidence-Grenze

T1–T9 sind durch lokale Implementierungs-, Unit- und Regressionstest-Evidence belegt. T10 ist offen: Echte Staging-/Production-Nachweise für installierte Units, Discord-Zustellung, Fehlerübungen, Queue-Isolation und gemessene Ende-zu-Ende-Zeiten stehen aus. Dieses Runbook dokumentiert nur die auszuführenden Schritte; in dieser lokalen Remediation wurden keine Staging- oder Production-Operationen vorgenommen.
