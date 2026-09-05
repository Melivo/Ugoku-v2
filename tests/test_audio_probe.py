import os
import subprocess
import sys
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from bot.health.audio_probe import probe_audio
from bot.health.cleanup import cleanup_with_deadline
from bot.vocal.session_manager import session_manager


class FakeSource:
    def __init__(self, packets):
        self.packets = iter(packets)
        self.cleanup = Mock()

    def read(self):
        return next(self.packets, b"")


class AudioProbeTests(unittest.IsolatedAsyncioTestCase):
    async def test_spotify_unavailable_is_na_without_queue_contact(self):
        before = dict(session_manager.server_sessions)
        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", False):
            result = await probe_audio(SimpleNamespace())
        self.assertIsNone(result.ok)
        self.assertEqual(result.service, "n/a")
        self.assertEqual(result.bytes_read, 0)
        self.assertEqual(session_manager.server_sessions, before)

    async def test_voice_e2e_decode_reads_bytes_and_cleans_every_repetition(self):
        stream = SimpleNamespace(close=Mock())
        librespot = SimpleNamespace(session=object(), get_stream=Mock(return_value=stream))
        bot = SimpleNamespace(spotify_sessions=SimpleNamespace(lp=librespot, sp=None))
        queue_before = dict(session_manager.server_sessions)
        sources = [FakeSource([b"abcd"]) for _ in range(3)]

        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True), patch(
            "bot.health.audio_probe.discord.FFmpegOpusAudio", side_effect=sources
        ) as ffmpeg:
            results = [
                await probe_audio(bot, timeout=0.5, bytes_to_read=4, track_id=object())
                for _ in range(3)
            ]

        self.assertTrue(all(result.ok is True for result in results))
        self.assertTrue(all(result.bytes_read >= 1 for result in results))
        self.assertEqual(ffmpeg.call_count, 3)
        for source in sources:
            source.cleanup.assert_called_once_with()
        self.assertEqual(stream.close.call_count, 3)
        self.assertEqual(session_manager.server_sessions, queue_before)

    async def test_hanging_ffmpeg_read_times_out_and_still_cleans_stream(self):
        released = threading.Event()

        class HangingSource:
            def __init__(self):
                self.cleaned = False

            def read(self):
                released.wait(1)
                return b"late"

            def cleanup(self):
                self.cleaned = True
                released.set()

        source = HangingSource()
        stream = SimpleNamespace(close=Mock())
        librespot = SimpleNamespace(session=object(), get_stream=Mock(return_value=stream))
        bot = SimpleNamespace(spotify_sessions=SimpleNamespace(lp=librespot, sp=None))
        started = time.monotonic()

        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True), patch(
            "bot.health.audio_probe.discord.FFmpegOpusAudio", return_value=source
        ):
            result = await probe_audio(
                bot, timeout=0.12, bytes_to_read=4, track_id=object()
            )

        released.set()
        self.assertFalse(result.ok)
        self.assertIn("timed out", result.error)
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(source.cleaned)
        stream.close.assert_called_once_with()

    async def test_invalid_limits_return_a_structured_failure(self):
        librespot = SimpleNamespace(session=object())
        bot = SimpleNamespace(spotify_sessions=SimpleNamespace(lp=librespot))
        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True):
            result = await probe_audio(bot, timeout=0, bytes_to_read=0)
        self.assertFalse(result.ok)
        self.assertIn("must be positive", result.error)

    async def test_missing_probe_track_is_failure_without_starting_ffmpeg(self):
        librespot = SimpleNamespace(session=object(), get_stream=Mock())
        bot = SimpleNamespace(
            spotify_sessions=SimpleNamespace(
                lp=librespot,
                sp=SimpleNamespace(search=None),
            )
        )
        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True), patch(
            "bot.health.audio_probe.discord.FFmpegOpusAudio"
        ) as ffmpeg:
            result = await probe_audio(
                bot, timeout=0.2, bytes_to_read=4, track_id=None
            )
        self.assertFalse(result.ok)
        self.assertEqual(result.service, "spotify")
        self.assertIn("no configured or discoverable Spotify probe track", result.error)
        librespot.get_stream.assert_not_called()
        ffmpeg.assert_not_called()

    async def test_missing_spotify_audio_session_is_failure_when_enabled(self):
        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True):
            result = await probe_audio(SimpleNamespace())

        self.assertFalse(result.ok)
        self.assertEqual(result.service, "spotify")
        self.assertIn("session unavailable", result.error)

    async def test_empty_or_failed_decoder_returns_structured_failure_and_cleans(self):
        for decoder, expected_error in (
            (FakeSource([]), "no Opus bytes"),
            (SimpleNamespace(read=Mock(side_effect=RuntimeError("decode failed")), cleanup=Mock()), "RuntimeError"),
        ):
            stream = SimpleNamespace(close=Mock())
            librespot = SimpleNamespace(
                session=object(), get_stream=Mock(return_value=stream)
            )
            bot = SimpleNamespace(
                spotify_sessions=SimpleNamespace(lp=librespot, sp=None)
            )
            with self.subTest(error=expected_error), patch(
                "bot.health.audio_probe.SPOTIFY_ENABLED", True
            ), patch(
                "bot.health.audio_probe.discord.FFmpegOpusAudio",
                return_value=decoder,
            ):
                result = await probe_audio(
                    bot, timeout=0.2, bytes_to_read=4, track_id=object()
                )
            self.assertFalse(result.ok)
            self.assertIn(expected_error, result.error)
            decoder.cleanup.assert_called_once_with()
            stream.close.assert_called_once_with()

    async def test_search_track_resolution_uses_spotify_api_result(self):
        stream = SimpleNamespace(close=Mock())
        source = FakeSource([b"opus"])
        librespot = SimpleNamespace(session=object(), get_stream=Mock(return_value=stream))
        spotify_api = SimpleNamespace(
            search=Mock(return_value={"tracks": {"items": [{"id": "track-1"}]}})
        )
        bot = SimpleNamespace(
            spotify_sessions=SimpleNamespace(lp=librespot, sp=spotify_api)
        )
        resolved = object()
        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True), patch(
            "bot.health.audio_probe.TrackId.from_uri", return_value=resolved
        ) as from_uri, patch(
            "bot.health.audio_probe.discord.FFmpegOpusAudio", return_value=source
        ):
            result = await probe_audio(
                bot, timeout=0.3, bytes_to_read=4, track_id=None
            )

        self.assertTrue(result.ok)
        spotify_api.search.assert_called_once_with(q="*", type="track", limit=1)
        from_uri.assert_called_once_with("spotify:track:track-1")
        librespot.get_stream.assert_called_once_with(resolved)

    async def test_real_child_process_is_killed_and_reaped_before_cleanup_deadline(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        source = SimpleNamespace(_process=child, cleanup=child.wait)
        started = time.monotonic()
        try:
            await cleanup_with_deadline(
                source, source.cleanup, started + 0.5, "controlled child"
            )
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=1)

        self.assertIsNotNone(child.poll())
        self.assertLess(time.monotonic() - started, 1.0)

    async def test_successful_cleanup_still_kills_and_reaps_live_child(self):
        process = SimpleNamespace(
            poll=Mock(return_value=None),
            kill=Mock(),
            wait=Mock(return_value=0),
        )
        resource = SimpleNamespace(_process=process)

        await cleanup_with_deadline(
            resource, Mock(), time.monotonic() + 0.5, "lying cleanup"
        )

        process.poll.assert_called_once_with()
        process.kill.assert_called_once_with()
        process.wait.assert_called_once()

    async def test_cleanup_exception_is_returned_as_probe_failure(self):
        stream = SimpleNamespace(close=Mock())
        source = FakeSource([b"opus"])
        source.cleanup.side_effect = RuntimeError("cleanup exploded")
        librespot = SimpleNamespace(session=object(), get_stream=Mock(return_value=stream))
        bot = SimpleNamespace(spotify_sessions=SimpleNamespace(lp=librespot, sp=None))

        with patch("bot.health.audio_probe.SPOTIFY_ENABLED", True), patch(
            "bot.health.audio_probe.discord.FFmpegOpusAudio", return_value=source
        ):
            result = await probe_audio(
                bot, timeout=0.3, bytes_to_read=4, track_id=object()
            )

        self.assertFalse(result.ok)
        self.assertIn("cleanup exploded", result.error)
