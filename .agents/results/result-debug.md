## Status: completed

## Summary

Statische Untersuchung des Production-Hängers. Die stärkste Root-Cause-Kette ist fehlende Ownership und fehlender Shutdown für Librespot-, Cache-, Voice- und FFmpeg-Ressourcen:

1. `main.py:37-62` initialisiert langlebige Ressourcen in `on_ready`, obwohl dieses Event mehrfach auftreten kann. `clean_cache_task()` ist endlos (`main.py:86-89`) und wird in `gather()` aufgenommen. `main.py:82-83` definiert ein nicht von Pycord dispatchtes `on_close`-Event; daher ist selbst der HTTP-Cleanup nicht zuverlässig erreichbar.
2. `bot/vocal/spotify.py:55-57` startet den Librespot-Listener ohne Task-Referenz. `bot/vocal/spotify.py:114` erzeugt einen dedizierten `ThreadPoolExecutor`, der nirgends heruntergefahren wird. Erfolgreiche Probe-Streams aus `bot/vocal/spotify.py:179-187` werden nicht geschlossen. Rekursive Retries in `bot/vocal/spotify.py:73-78` und `bot/vocal/spotify.py:152-169` sind unbeschränkt.
3. Bei aggressivem Caching (`config.py:48`) startet `bot/vocal/track_dataclass.py:240-245` pro Track einen losgelösten Cache-Task. Der Worker liest in `bot/vocal/track_dataclass.py:257-288` bis EOF, während `bot/vocal/track_dataclass.py:248` die einzige am Track sichtbare Librespot-Streamreferenz durch einen `Path` ersetzt. `close_stream()` (`bot/vocal/track_dataclass.py:326-340`) kann den tatsächlich noch vom Worker gelesenen Stream danach nicht mehr schließen. Task-Cancellation beendet `asyncio.to_thread`-Arbeit nicht. So sammeln sich blockierte Python-Executor-Threads und Librespot-Verbindungen an.
4. Jede Wiedergabe startet FFmpeg in `bot/vocal/server_session.py:274-288`. Cleanup ruft synchron `source.cleanup()` auf (`bot/vocal/server_session.py:625-638`) und wird auch aus Event-Loop-Coroutinen aufgerufen (`bot/vocal/server_session.py:271`, `667-671`, `699-727`). Pycords FFmpeg-Cleanup führt `kill()` plus blockierendes `communicate()` aus. Ein hängender Cleanup kann daher den Event Loop blockieren, obwohl das Gateway seine Session auf Transportebene weiter fortsetzt. Das erklärt, warum auch der Spotify-unabhängige `/ping`-Pfad (`commands/other/ping.py:18-29`) nicht mehr reagiert.
5. `stop_playback()` wartet unbegrenzt auf einen Callback (`bot/vocal/server_session.py:484-505`). Der Callback läuft erst, wenn der AudioPlayer-Thread seinen möglicherweise blockierenden FFmpeg-Read beendet. Das blockiert Voice-Interaktionen und Cleanup.
6. Reconnects verschärfen die Akkumulation: `bot/vocal/session_manager.py:43-62` entfernt die alte Session und startet deren Cleanup fire-and-forget, bevor die neue Session gespeichert wird. Das alte `clean_session()` führt später ein unbedingtes `pop(guild_id)` aus (`bot/vocal/server_session.py:724`) und kann dadurch die neue Session aus dem Manager entfernen. Deren Tasks, VoiceClient und FFmpeg-Prozess bleiben dann ohne erreichbaren Owner. Zusätzlich ist `connect_task` bei bereits bestehender Voice-Verbindung und fehlendem Manager-Eintrag nicht initialisiert (`bot/vocal/session_manager.py:43-58`).
7. Beim SIGTERM stoppt Pycords `bot.run()` den Loop und cancelt Tasks; Cancellation stoppt laufende `to_thread`-Worker nicht. Wegen des nie ausgeführten anwendungsspezifischen Shutdowns bleiben der dedizierte Librespot-Executor, Cache-Worker und FFmpeg-Kinder aktiv. Nicht-daemonisierte Executor-Threads halten Python am Leben; `deploy/ugoku.service:14` erzwingt nach 30 Sekunden SIGKILL für die ganze cgroup. Das beobachtete systemd-Bild ist damit konsistent.

## Minimaler Fixvorschlag

1. Einen einmaligen, expliziten Lifecycle statt Ressourcenaufbau in ungeschütztem `on_ready` verwenden. Alle Hintergrundtasks referenzieren. Beim echten `Bot.close()` beziehungsweise in `async main()`/`finally` in dieser Reihenfolge schließen: ServerSessions, Cache-Tasks und deren Streams, Librespot-Listener, Librespot-Session und Executor, HTTP-/Deezer-Clients, danach `super().close()`.
2. Im aggressiven Spotify-Cache den ursprünglichen Stream und den Cache-Task separat am `Track` halten. `store_spotify_stream` bekommt den Stream explizit. `Track.close()` schließt zuerst diesen Stream und wartet begrenzt auf den Cache-Task; erst danach darf die Referenz verworfen werden. Als sofortige Production-Mitigation kann aggressives Caching deaktiviert werden, das ersetzt aber den Lifecycle-Fix nicht.
3. `stop_event.wait()` mit Timeout versehen; beim Timeout FFmpeg explizit bereinigen. Blockierendes `source.cleanup()` nicht synchron auf dem Event Loop ausführen.
4. Session-Ersetzung serialisieren oder mindestens beim Entfernen identitätsprüfen: nur poppen, wenn `manager.server_sessions.get(guild_id) is self`; `connect_task = None` vor der Verzweigung setzen. Alte Session-Cleanups müssen owned/awaited sein.

## Teststrategie

- Startup-Idempotenz: `on_ready`/Initialisierung zweimal auslösen; genau eine SpotifySessions-Instanz, ein Listener und ein Cache-Loop dürfen existieren.
- Cache-Regression: blockierender Fake-Librespot-Stream, dessen `close()` den Read freigibt. Nach `Track.close()` müssen Cache-Task und Worker innerhalb eines kurzen Timeouts beendet sein; ohne Fix hängt der Test.
- Session-Race: alte Session ersetzen, deren Cleanup verzögern, dann abschließen lassen. Der Manager muss weiterhin exakt auf die neue Session zeigen.
- Stop-Timeout: Fake-VoiceClient ruft den `after`-Callback nie auf. `stop_playback`/`clean_session` müssen begrenzt zurückkehren und FFmpeg-Cleanup auslösen.
- Event-Loop-Reaktivität: während eines hängenden Fake-FFmpeg-Cleanups einen 50-ms-Sentinel und den `/ping`-Handler ausführen; der Sentinel darf nicht aussetzen.
- Linux-Integration: Testprozess mit Fake/echtem kurzlebigem FFmpeg starten, SIGTERM senden und prüfen, dass Parent und Kinder deutlich vor `TimeoutStopSec=30` verschwinden.

## Ähnliche Muster

- `commands/download/spotify_download.py:58-65`: Librespot-Stream wird vollständig in `to_thread` gelesen, aber nie in `finally` geschlossen.
- `deezer_decryption/api.py:33-40`: losgelöster endloser Refresh-Task ohne Referenz; `httpx.AsyncClient` aus `deezer_decryption/api.py:21` wird nicht geschlossen.
- `deezer_decryption/chunked_input_stream.py:21-22`: globale HTTP-Clients ohne globalen Shutdown.
- `main.py:50-58`: erneutes `on_ready` ersetzt `bot.spotify`/`bot.deezer`; alte Instanzen und deren Tasks bleiben erreichbar über ihre laufenden Tasks/Threads.
- Viele fire-and-forget `create_task`-Aufrufe sind nicht ursächlich gleich kritisch, aber die Voice-Pfade in `bot/vocal/session_manager.py:44-62` und `bot/vocal/track_dataclass.py:222-242` benötigen Ownership und Fehlerbeobachtung.
- `requirements.txt:1-3` pinnt weder Pycord noch den Librespot-Git-Commit exakt; dadurch ist das konkrete Subprozess-/Shutdown-Verhalten in Production nicht reproduzierbar festgelegt.

## Reproduktion und Evidenzgrenzen

- Keine vorhandenen Tests gefunden; lokales `python` enthält `discord` nicht, daher kein vollständiger Botstart.
- Isoliert bestätigt: Cancellation eines `asyncio.to_thread`-Tasks stoppt den Worker nicht; `ThreadPoolExecutor`-Worker sind nicht daemonisiert.
- Keine Production-Logs, PID-Bäume oder Thread-Dumps lagen im Workspace vor. Die Diagnose ist deshalb code- und beobachtungsbasiert; der Cache-/Lifecycle-Leak ist direkt belegt, während der genaue erste Event-Loop-Blocker ohne Stackdump nicht eindeutig zwischen synchronem FFmpeg-Cleanup und Ressourcenerschöpfung unterschieden werden kann.

## Files changed

- Nur dieses vorgeschriebene Ergebnisartefakt: `.agents/results/result-debug.md`
- Keine Anwendungs-, Konfigurations- oder Testdateien geändert.
- Bereits vor der Untersuchung vorhanden: modifiziertes `config.py` sowie unversionierte `.agents/`, `.opencode/`, `.serena/`, `deploy/`.

## Acceptance criteria checklist

- [x] Prozess-, Subprocess- und asyncio-Verwaltung mit konkreten Referenzen untersucht
- [x] Ursache der Kindprozess-/Thread-Akkumulation beschrieben
- [x] Pfad zu blockierten Interaktionen und Shutdown-Timeout beschrieben
- [x] Minimalen Fix und Production-Mitigation vorgeschlagen
- [x] Regressionsteststrategie angegeben
- [x] Ähnliche Muster repositoryweit gescannt
- [x] Keine Anwendungsdateien geändert
