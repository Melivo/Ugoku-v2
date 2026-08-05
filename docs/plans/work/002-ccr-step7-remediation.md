# CCR-Step-7-Remediation

> Die zweiten HIGH-/MEDIUM-Befunde werden an Restart-, Alert-, Recovery- und Ressourcen-Lifecycle-Wurzeln behoben.

**Status**: Completed
**Created**: 2026-08-05
**Owner**: backend

## Goal
Genau ein nicht blockierender Restart pro Incident, durable und geordnete Alert-Zustellung, strikt gesundheitsgegatete Recovery innerhalb von 300 Sekunden sowie atomarer Cleanup und Initialisierungs-Rollback.

## Context
Der zweite CCR-Safety-Review fand vier HIGH- und drei MEDIUM-Luecken in `scripts/healthcheck.py`, systemd-Artefakten, FFmpeg-Cleanup und Spotify-Initialisierung. Bestehende Nutzeranderungen bleiben erhalten.

## Constraints
- Bestehenden Python-/py-cord-/systemd-Stack beibehalten.
- Keine neue Fremdabhaengigkeit.
- Nur die betroffenen Runtime-, Deploy-, Test- und Vertragsdateien aendern.
- Alert-Ereignisse erst nach bestaetigtem Webhook-Erfolg als geliefert behandeln.

## Tasks

| # | Task | Agent | Priority | Status | Dependencies |
|---|---|---|---|---|---|
| 1 | Atomare Alert-Outbox und deduplizierten Restart-Zustand implementieren | backend | 1 | DONE | — |
| 2 | FFmpeg-Cleanup erst nach erfolgreichem Cleanup committen | backend | 1 | DONE | — |
| 3 | TaskGroup-artige Initialisierung mit Rollback implementieren | backend | 1 | DONE | — |
| 4 | Strikten post-READY-Recovery- und systemd-Vertrag herstellen | backend | 2 | DONE | 1 |
| 5 | Plan, Runbook und Abnahmevertrag synchronisieren | docs | 3 | DONE | 4 |
| 6 | Regressionen und vollstaendige Suite ausfuehren | qa | 3 | DONE | 1, 2, 3, 4 |

## Done When
- [x] `systemctl --no-block` und exakt passendes sudoers-Recht sind dedupliziert.
- [x] OUTAGE/RESTART/RECOVERY bleiben bis Zustellung persistent pending; Watchdog liefert RESTART.
- [x] Nur strikt gesunder, frischer post-READY-State kann Recovery ausloesen.
- [x] Fehlende alte `boot_id` blockiert einen nach Incident-Beginn geschriebenen gesunden Snapshot nicht.
- [x] FFmpeg-Quellen und Spotify-Ressourcen bleiben bis Cleanup/Rollback erreichbar.
- [x] `UMask=0077` ist gesetzt.
- [x] Vollstaendige Tests bestehen.

## Decision Log

| Date | Decision | Rationale |
|---|---|---|
| 2026-08-05 | Outbox bleibt dateibasiert und unter dem bestehenden Incident-Lock | Erhaelt den Single-Owner-Vertrag und benoetigt keine neue Infrastruktur. |
| 2026-08-05 | Recovery-Hook wird nach `Type=notify` READY mit strengem Health-Prädikat ausgefuehrt | Erfuellt die SLA, ohne Grace-basierte false recovery. |

## Progress Notes

- [2026-08-05] Plan analysiert und durch die ausdrueckliche Sofortausfuehrungsanweisung freigegeben.
- [2026-08-05] Implementierung abgeschlossen; 52 Tests, Compile-Check, Ruff, Dependency-Check und sudoers-Parsing erfolgreich.
