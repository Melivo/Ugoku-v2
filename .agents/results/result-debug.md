## Status: completed

## Zusammenfassung

- **Librespot:** Keine weitere bestätigte verwundbare Stelle. Der einzige Produktionsaufruf von `content_feeder().load(...)` ist zentral verriegelt; sämtliche drei Produktionspfade zu `get_stream()` laufen darüber.
- **Spotify-Pagination:** Der zentrale Playlist-/Liked-Songs-Pfad ist korrigiert und vollständig paginiert. Zwei direkte Spotipy-Abrufe außerhalb dieses Pfads bleiben bestätigt unvollständig und benötigen separate Fixes.
- Es wurde kein Produktions- oder Testcode geändert.

## Befunde

### MEDIUM — Fix erforderlich

1. **`commands/vocal/search.py:53-66`** — Der Playlist-URL-Pfad ruft `playlist_tracks()` direkt auf und verarbeitet ausschließlich `playlist_tracks["items"]`; `next` wird nie verfolgt. Spotipy verwendet hier standardmäßig `limit=50`. `/search` und „Play all“ schneiden Playlists mit mehr als 50 Einträgen daher bestätigt ab.
2. **`commands/vocal/sp_playlist.py:125-129`** — `current_user_playlists()` wird genau einmal aufgerufen und nur dessen erste Seite ausgewertet (Spotipy-Standard: 50). Spätere Playlist-Seiten eines Kontos sind nicht auswählbar. Der Fix muss API-Pagination mit UI-Pagination bzw. Begrenzung des Discord-Selects (`commands/vocal/sp_playlist.py:28-40`) kombinieren.

### Geprüft und abgedeckt

- **`bot/vocal/spotify.py:137,240-248`** — Instanzweiter `asyncio.Lock` umfasst den vollständigen einzigen `content_feeder().load(...)`-Aufruf.
- **`bot/vocal/spotify.py:222`, `bot/vocal/spotify.py:260`, `bot/health/audio_probe.py:90`** — Keepalive, Wiedergabe und Health-Probe rufen ausschließlich den verriegelten `Librespot.get_stream()`-Pfad auf; kein direkter Feeder-Bypass gefunden.
- **`bot/vocal/spotify.py:353-373`** — Standard-Playlists und „Liked Songs“ folgen `sp_.next(...)` bis `next` leer ist.
- **`bot/vocal/audio_service_handlers.py:74-83`, `commands/vocal/sp_playlist.py:49-55`, `bot/utils.py:677`, `commands/download/spotify_download.py:48`, `commands/vocal/lyrics.py:83`** — Diese Produktionsverbraucher verwenden den zentralen `Spotify.get_tracks()`-Pfad. Die Playlist-Metadatenabfrage in `commands/vocal/search.py:50-52` benötigt selbst keine Track-Pagination.

## Verwendete Befehle und Tests

- Native Grep-/AST-Scans über `bot/**/*.py` und `commands/**/*.py` nach `content_feeder`, `get_stream`, `playlist_tracks`, `current_user_playlists`, `current_user_saved_tracks` und `next`; Serena-MCP war in dieser Sitzung nicht verbunden, `rg` nicht installiert.
- `venv\Scripts\python.exe -m unittest tests.test_spotify -v` — **2/2 bestanden**.
- `venv\Scripts\python.exe -m unittest tests.test_spotify tests.test_audio_probe tests.test_main_initialization -v` — **19/19 bestanden**.
- `venv\Scripts\python.exe -c "import inspect, spotipy; ..."` — bestätigte `playlist_tracks(..., limit=50, ...)` und `current_user_playlists(limit=50, ...)`.
- `git diff -- bot/vocal/spotify.py commands/vocal/search.py commands/vocal/sp_playlist.py tests/test_spotify.py` und `git diff --check` — bestehende Fix-Differenz geprüft; Diff-Check erfolgreich (nur LF/CRLF-Hinweise).
- `oma state:verify --workflow review --checkpoint severity-classification` — Entscheidung vorhanden.

## Geänderte Dateien

- `.agents/results/result-debug.md` — dieser Prüfbericht.
- Kein Produktions- oder Testcode durch diesen Scan geändert. `oma state:emit` schrieb ausschließlich Workflow-Laufzustand unter `.agents/state/`.

## Acceptance Criteria

- [x] Alle Produktionsreferenzen auf `content_feeder().load` und `get_stream()` erfasst.
- [x] Alle Spotify-Playlist-/Liked-Songs-Abrufe und Produktionsverbraucher erfasst.
- [x] Verbleibende bestätigte Schwachstellen mit Datei und Zeile benannt.
- [x] Fixbedarf eindeutig bewertet: zwei Pagination-Fixes erforderlich, kein weiterer Librespot-Concurrency-Fix.
- [x] Relevante Regressionstests ausgeführt.
- [x] Kein Produktions- oder Testcode geändert.
