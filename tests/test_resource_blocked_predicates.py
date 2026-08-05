import os
import time
import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from bot.health.monitor import HealthMonitor
from bot.vocal.session_manager import session_manager


class TaskState:
    def __init__(self, done=False):
        self._done = done

    def done(self):
        return self._done


def bot_with_spotify(spotify_sessions=None):
    return SimpleNamespace(
        is_ready=lambda: True,
        is_closed=lambda: False,
        latency=0.01,
        ws=SimpleNamespace(open=True, closed=False),
        spotify_sessions=spotify_sessions,
    )


class ResourceBlockedPredicateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_sessions = dict(session_manager.server_sessions)
        session_manager.server_sessions.clear()

    def tearDown(self):
        session_manager.server_sessions.clear()
        session_manager.server_sessions.update(self.original_sessions)

    async def test_voice_connect_stuck_has_highest_resource_priority(self):
        session_manager.server_sessions[1] = SimpleNamespace(
            guild_id=1,
            voice_client=None,
            ffmpeg_sources=deque([object()]),
            connect_task=TaskState(done=False),
            connect_started_monotonic=time.monotonic() - 120,
        )
        with patch("bot.health.monitor.SPOTIFY_ENABLED", False):
            state = await HealthMonitor(bot_with_spotify()).snapshot()

        self.assertEqual(state["voice"]["stuck_connects"], 1)
        self.assertEqual(state["ffmpeg"]["orphan_sources"], 1)
        self.assertEqual(
            state["resource_blocked"],
            {
                "blocked": True,
                "reason": "voice",
                "since_monotonic": state["resource_blocked"]["since_monotonic"],
            },
        )
        self.assertIsNotNone(state["resource_blocked"]["since_monotonic"])

    async def test_ffmpeg_orphan_is_reported(self):
        voice = SimpleNamespace(is_playing=lambda: False, source=None)
        session_manager.server_sessions[2] = SimpleNamespace(
            guild_id=2,
            voice_client=voice,
            ffmpeg_sources=deque([object()]),
            connect_task=None,
        )
        with patch("bot.health.monitor.SPOTIFY_ENABLED", False):
            state = await HealthMonitor(bot_with_spotify()).snapshot()
        self.assertTrue(state["resource_blocked"]["blocked"])
        self.assertEqual(state["resource_blocked"]["reason"], "ffmpeg")

    async def test_paused_active_source_is_not_an_ffmpeg_orphan(self):
        source = object()
        voice = SimpleNamespace(
            is_playing=lambda: False,
            is_paused=lambda: True,
            source=source,
        )
        session_manager.server_sessions[2] = SimpleNamespace(
            guild_id=2,
            voice_client=voice,
            ffmpeg_sources=deque([source]),
            connect_task=None,
        )
        with patch("bot.health.monitor.SPOTIFY_ENABLED", False):
            state = await HealthMonitor(bot_with_spotify()).snapshot()

        self.assertEqual(state["ffmpeg"]["orphan_sources"], 0)
        self.assertFalse(state["resource_blocked"]["blocked"])

    async def test_done_and_stale_librespot_listener_are_reported(self):
        for listener in (
            TaskState(done=True),
            TaskState(done=False),
        ):
            spotify_sessions = SimpleNamespace(
                lp=SimpleNamespace(session=object()),
                listener_task=listener,
                listener_last_beat_monotonic=time.monotonic() - 120,
            )
            with self.subTest(done=listener.done()), patch(
                "bot.health.monitor.SPOTIFY_ENABLED", True
            ):
                state = await HealthMonitor(
                    bot_with_spotify(spotify_sessions)
                ).snapshot()
            self.assertTrue(state["resource_blocked"]["blocked"])
            self.assertEqual(state["resource_blocked"]["reason"], "librespot")
