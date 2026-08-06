# Debug-Fortschritt

- Status: abgeschlossen
- Aktion: Pycord-Signal-/Cleanup-Reihenfolge diagnostiziert, Signalpfad auf den bestehenden asynchronen `bot.close()`-Lifecycle umgestellt und Regressionstest ergänzt.
- Geänderte Produktdateien: `main.py`, `tests/test_shutdown_budget.py`
- Verifikation: gezielte Tests 6/6; vollständige Suite 64/64 plus 25 Subtests; `py_compile` und `git diff --check` erfolgreich.
