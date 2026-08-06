---
oma-docs: skip
---

# Bug: Search Play-all Stops After First Spotify Playlist Page

**Date Reported**: 2026-08-07  
**Date Fixed**: 2026-08-07  
**Assignee**: Backend Agent  
**Severity**: MEDIUM  
**Status**: FIXED

## Problem

Spotify playlist URL searches passed only the first `playlist_tracks()` page to
the track conversion used by Play all. Spotify limits that page to 50 entries,
so longer playlists silently omitted every later track.

## Root Cause

`Search.execute_search()` iterated `playlist_tracks["items"]` once and never
checked the response's `next` link. The analogous Spotify service path already
used `sp.next(page)` until no next page remained.

## Fix

The search command now processes each page, preserves the existing `item` /
`track` entry filtering, and retrieves subsequent pages with
`asyncio.to_thread(spotify.sessions.sp.next, playlist_tracks)`.

## Regression Coverage

`tests/test_vocal_search.py` supplies a 50-entry first page and a one-entry
second page. Before the fix it failed with `50 != 51`; after the fix all 51
entries are converted and `sp.next(first_page)` is verified.

## Verification

- Focused regression test: PASS (1/1)
- Search plus existing Spotify pagination tests: PASS (3/3)
- Python compilation: PASS
- Diff whitespace check: PASS (LF-to-CRLF notice only)

## Scope and Prevention

Only `commands/vocal/search.py` and its focused test were changed. The separate
user-playlist UI pagination in `commands/vocal/sp_playlist.py` was intentionally
left for UX design. Future direct Spotipy paging-object consumers should follow
`next` links until absent and include a test crossing the provider page limit.
