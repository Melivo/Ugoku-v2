import asyncio
import os
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from bot.vocal.spotify import Librespot, Spotify


class FakeContentFeeder:
    def __init__(self):
        self._state_lock = threading.Lock()
        self._shared_track_id = None
        self.in_flight = 0
        self.max_in_flight = 0

    def load(self, track_id, _quality, _preload, _listener):
        with self._state_lock:
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
            self._shared_track_id = track_id

        time.sleep(0.02)

        with self._state_lock:
            loaded_track_id = self._shared_track_id
            self.in_flight -= 1

        return SimpleNamespace(
            input_stream=SimpleNamespace(
                stream=lambda: f"stream:{loaded_track_id}"
            )
        )


class LibrespotStreamTests(unittest.IsolatedAsyncioTestCase):
    async def test_concurrent_stream_loads_are_serialized_and_keep_their_results(self):
        feeder = FakeContentFeeder()
        librespot = Librespot()
        librespot.session = SimpleNamespace(content_feeder=lambda: feeder)
        track_ids = [f"track-{index}" for index in range(6)]

        try:
            streams = await asyncio.gather(
                *(librespot.get_stream(track_id) for track_id in track_ids)
            )
        finally:
            librespot.executor.shutdown(wait=True, cancel_futures=True)

        self.assertEqual(feeder.max_in_flight, 1)
        self.assertEqual(streams, [f"stream:{track_id}" for track_id in track_ids])

    async def test_listener_refreshes_heartbeat_after_successful_read(self):
        librespot = Librespot()
        stream = SimpleNamespace(read=Mock(return_value=b"x"))
        started = time.monotonic()

        try:
            with (
                patch.object(
                    librespot,
                    "get_stream",
                    AsyncMock(return_value=stream),
                ),
                patch(
                    "bot.vocal.spotify.asyncio.sleep",
                    AsyncMock(side_effect=asyncio.CancelledError),
                ),
            ):
                with self.assertRaises(asyncio.CancelledError):
                    await librespot.listen_to_session()
        finally:
            librespot.executor.shutdown(wait=True, cancel_futures=True)

        self.assertGreaterEqual(librespot.listener_last_beat_monotonic, started)
        stream.read.assert_called_once_with(1)


class SpotifyPlaylistTests(unittest.IsolatedAsyncioTestCase):
    async def test_playlist_tracks_aggregates_all_pages(self):
        first_page = {
            "items": [{"track": {"id": "track-1"}}],
            "next": "page-2",
        }
        second_page = {
            "items": [{"item": {"id": "track-2"}}],
            "next": "page-3",
        }
        third_page = {
            "items": [{"track": {"id": "track-3"}}],
            "next": None,
        }
        spotify_api = SimpleNamespace(
            playlist_tracks=Mock(return_value=first_page),
            next=Mock(side_effect=[second_page, third_page]),
        )
        spotify = Spotify(SimpleNamespace(sp=spotify_api))

        with patch.object(
            spotify, "get_track", side_effect=lambda track: track["id"]
        ):
            tracks = await spotify.get_tracks(id_="playlist-1", type="playlist")

        self.assertEqual(tracks, ["track-1", "track-2", "track-3"])
        spotify_api.playlist_tracks.assert_called_once_with(
            playlist_id="playlist-1", offset=0
        )
        self.assertEqual(
            spotify_api.next.call_args_list,
            [call(first_page), call(second_page)],
        )
