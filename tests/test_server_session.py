import asyncio
import subprocess
import sys
import threading
import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from bot.vocal.server_session import ServerSession


class ServerSessionCleanupTests(unittest.IsolatedAsyncioTestCase):
    async def test_old_session_cleanup_keeps_replacement(self):
        old_session = object.__new__(ServerSession)
        replacement = object()
        manager = type("Manager", (), {"server_sessions": {1: replacement}})()

        old_session.guild_id = 1
        old_session.session_manager = manager
        old_session.stop_playback = AsyncMock()
        old_session.now_playing_message = None
        old_session.now_playing_view = None
        old_session.wrong_track_views = []
        old_session.voice_client = None
        old_session.cleanup_task = None
        old_session.connect_task = None
        old_session.dummy_load = None
        old_session.close_streams = AsyncMock()
        old_session.clean_ffmpeg_sources = AsyncMock()
        old_session.bot = object()
        old_session.deezer_download = None

        await old_session.clean_session()

        self.assertIs(manager.server_sessions[1], replacement)

    async def test_paused_source_is_kept_active_during_cleanup(self):
        session = object.__new__(ServerSession)
        source = SimpleNamespace(cleanup=Mock())
        session.ffmpeg_sources = deque([source])
        session.ffmpeg_cleanup_lock = asyncio.Lock()
        session.voice_client = SimpleNamespace(
            is_connected=lambda: True,
            is_playing=lambda: False,
            is_paused=lambda: True,
        )

        await session.clean_ffmpeg_sources()

        self.assertEqual(list(session.ffmpeg_sources), [source])
        source.cleanup.assert_not_called()

    async def test_clean_session_keeps_hanging_source_visible_until_child_is_reaped(self):
        child = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        source = SimpleNamespace(_process=child, cleanup=child.wait)
        session = object.__new__(ServerSession)
        manager = type("Manager", (), {"server_sessions": {9: session}})()
        session.guild_id = 9
        session.session_manager = manager
        session.stop_playback = AsyncMock()
        session.now_playing_message = None
        session.now_playing_view = None
        session.wrong_track_views = []
        session.voice_client = None
        session.cleanup_task = None
        session.connect_task = None
        session.dummy_load = None
        session.close_streams = AsyncMock()
        session.ffmpeg_sources = deque([source])
        session.ffmpeg_cleanup_lock = asyncio.Lock()
        session.bot = object()
        session.deezer_download = None

        try:
            with patch("bot.vocal.server_session.HEALTH_FORCE_CLEANUP_BUDGET", 0.5):
                cleanup_task = asyncio.create_task(session.clean_session())
                await asyncio.sleep(0.05)
                self.assertIn(source, session.ffmpeg_sources)
                await cleanup_task
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=1)

        self.assertIsNotNone(child.poll())
        self.assertNotIn(source, session.ffmpeg_sources)

    async def test_failed_ffmpeg_cleanup_keeps_source_and_session_discoverable(self):
        session = object.__new__(ServerSession)
        source = SimpleNamespace(cleanup=Mock(side_effect=RuntimeError("cleanup failed")))
        manager = type("Manager", (), {"server_sessions": {11: session}})()
        session.guild_id = 11
        session.session_manager = manager
        session.stop_playback = AsyncMock()
        session.now_playing_message = None
        session.now_playing_view = None
        session.wrong_track_views = []
        session.voice_client = None
        session.cleanup_task = None
        session.connect_task = None
        session.dummy_load = None
        session.close_streams = AsyncMock()
        session.ffmpeg_sources = deque([source])
        session.ffmpeg_cleanup_lock = asyncio.Lock()
        session.bot = object()
        session.deezer_download = None

        with self.assertRaisesRegex(RuntimeError, "cleanup failed"):
            await session.clean_session()

        self.assertEqual(list(session.ffmpeg_sources), [source])
        self.assertIs(manager.server_sessions[11], session)

    async def test_concurrent_ffmpeg_cleanup_only_cleans_source_once(self):
        cleanup_started = threading.Event()
        allow_cleanup = threading.Event()

        def cleanup():
            cleanup_started.set()
            allow_cleanup.wait(timeout=1)

        session = object.__new__(ServerSession)
        source = SimpleNamespace(cleanup=Mock(side_effect=cleanup))
        session.ffmpeg_sources = deque([source])
        session.ffmpeg_cleanup_lock = asyncio.Lock()
        session.voice_client = None

        first_cleanup = asyncio.create_task(session.clean_ffmpeg_sources())
        self.assertTrue(await asyncio.to_thread(cleanup_started.wait, 1))
        second_cleanup = asyncio.create_task(session.clean_ffmpeg_sources())
        await asyncio.sleep(0)
        allow_cleanup.set()
        await asyncio.gather(first_cleanup, second_cleanup)

        source.cleanup.assert_called_once_with()
        self.assertEqual(list(session.ffmpeg_sources), [])
