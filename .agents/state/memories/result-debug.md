## Status: completed

## Summary

Pycords `Bot.run()` ersetzt unter Linux die SIGINT-/SIGTERM-Handler durch `loop.stop`. Bei systemd-SIGTERM endet der aktive Loop deshalb, bevor der überschreibende `bot.close = close_bot`-Lifecycle mit Spotify-, HTTP- und anschließendem `original_close()` abgeschlossen ist. Pycord versucht die bereits cancellierten Futures danach in `_cleanup_loop()` mittels `run_until_complete()` einzusammeln; daraus folgen der beobachtete RuntimeError sowie pending/unclosed Ressourcen.

Der minimale Fix stellt nach Pycords Handler-Installation auf dem ersten Loop-Tick SIGINT/SIGTERM auf eine einmalige Task für den vorhandenen `bot.close()`-Lifecycle um. Der Loop läuft damit bis `close_bot()` und `original_close()` fertig sind; die bestehende Cleanup-Reihenfolge, Budgets, Monitoring- und Benutzungsfunktionen bleiben unverändert.

## Files changed

- `main.py`: asynchronen Shutdown-Signalpfad ergänzt und Start über `run_bot()` geführt.
- `tests/test_shutdown_budget.py`: Regressionstest für Pycords Handler-Reihenfolge und den SIGTERM→`bot.close()`-Pfad ergänzt.
- `.agents/results/result-debug.md`: Debug-Ergebnis.
- `.agents/state/memories/progress-debug.md`, `.agents/state/memories/result-debug.md`: Laufstatus und Übergabe.

## Test results

- Gezielt: `6 passed` (`test_shutdown_budget.py`, `test_close_cleanup_disconnect.py`).
- Vollständig: `64 passed, 25 subtests passed`.
- Syntax: `python -m py_compile main.py tests/test_shutdown_budget.py` erfolgreich.
- Diff-Prüfung: `git diff --check` erfolgreich.

## Similar-pattern scan

Keine weitere eigene `loop.stop`-/`run_until_complete`-/Signalhandler-Implementierung im Python-Anwendungscode gefunden. Der einzige `bot.run(BOT_TOKEN)`-Pfad wird vom Fix abgedeckt.

## Acceptance criteria checklist

- [x] Reproduzierten Lifecycle-Fehler und vorhandene Tests untersucht.
- [x] `bot.close = close_bot`, `original_close()` und Pycord-`run()`-Cleanup nachvollzogen.
- [x] Root Cause statt Warnungssymptome behoben.
- [x] Minimaler Fix ohne Monitoring- oder Benutzungsänderung implementiert.
- [x] Regressionstest ergänzt.
- [x] Gezielte und vollständige Tests erfolgreich.
- [x] Repository nach ähnlichen Mustern gescannt.
