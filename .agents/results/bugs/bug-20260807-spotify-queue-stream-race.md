---
oma-docs: skip
---

# Bug: Spotify Queue Skips Tracks After the First Song

**Date Reported**: 2026-08-07  
**Date Fixed**: 2026-08-07  
**Severity**: HIGH  
**Status**: FIXED

## Symptom

When a Spotify playlist was added to the Discord queue, the first track could
play, while later tracks were reported as unavailable and skipped. Playlist
imports also stopped after Spotify's first 50-item response page.

## Root Cause

Playback, preloading, keepalive, and audio health probing concurrently invoked
the Librespot content feeder. The installed Librespot fork shares its audio-key
callback queue, allowing a concurrent request to consume another request's key.
The resulting stream load failure was subsequently classified as an unavailable
track. Separately, Spotify paging responses were not followed.

## Fix

- `bot/vocal/spotify.py` serializes each content-feeder load through a
  `Librespot`-owned `asyncio.Lock`.
- `bot/vocal/spotify.py` follows all Spotify playlist response pages.
- `commands/vocal/search.py` follows playlist pages in the Play all command.

## Regression Coverage

- `tests/test_spotify.py` verifies concurrent stream loads remain serialized
  and return their respective results.
- `tests/test_spotify.py` verifies playlist pages aggregate past 50 tracks.
- `tests/test_vocal_search.py` verifies Play all aggregates past 50 tracks.

## Verification

`venv\\Scripts\\python.exe -m unittest tests.test_vocal_search tests.test_spotify -v`
completed successfully: 3 tests passed.

## Similar Patterns

`commands/vocal/sp_playlist.py` only retrieves the first 50 user playlists.
This does not cause queue playback failures, but paging it needs a separate
Discord selection UI design and was intentionally left unchanged.
