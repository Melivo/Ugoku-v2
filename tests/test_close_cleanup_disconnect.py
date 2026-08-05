import asyncio
import os
import time
import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import main


class CloseCleanupDisconnectTests(unittest.IsolatedAsyncioTestCase):
    async def test_force_session_cleanup_cancels_tasks_children_and_disconnects(self):
        tasks = [asyncio.create_task(asyncio.sleep(10)) for _ in range(3)]
        source = SimpleNamespace(cleanup=Mock())
        voice = SimpleNamespace(
            stop=Mock(),
            disconnect=AsyncMock(),
            cleanup=Mock(),
        )
        session = SimpleNamespace(
            guild_id=123,
            cleanup_task=tasks[0],
            connect_task=tasks[1],
            dummy_load=tasks[2],
            ffmpeg_sources=deque([source]),
            voice_client=voice,
        )
        original = dict(main.session_manager.server_sessions)
        main.session_manager.server_sessions.clear()
        main.session_manager.server_sessions[123] = session
        try:
            await main._force_session_cleanup(session)
            await asyncio.sleep(0)
        finally:
            main.session_manager.server_sessions.clear()
            main.session_manager.server_sessions.update(original)

        self.assertTrue(all(task.cancelled() for task in tasks))
        source.cleanup.assert_called_once_with()
        voice.stop.assert_called_once_with()
        voice.disconnect.assert_awaited_once_with(force=True)
        voice.cleanup.assert_called_once_with()
        self.assertNotIn(123, main.session_manager.server_sessions)

    async def test_disconnect_without_force_keyword_and_librespot_child_cleanup(self):
        disconnect = AsyncMock(side_effect=[TypeError("legacy signature"), None])
        session = SimpleNamespace(
            guild_id=5,
            cleanup_task=None,
            connect_task=None,
            dummy_load=None,
            ffmpeg_sources=deque(),
            voice_client=SimpleNamespace(
                stop=Mock(), disconnect=disconnect, cleanup=Mock()
            ),
        )
        await main._force_session_cleanup(session)
        self.assertEqual(disconnect.await_count, 2)
        self.assertEqual(disconnect.await_args_list[0].kwargs, {"force": True})
        self.assertEqual(disconnect.await_args_list[1].kwargs, {})

        listener = asyncio.create_task(asyncio.sleep(10))
        close = Mock()
        shutdown = Mock()
        spotify = SimpleNamespace(
            listener_task=listener,
            lp=SimpleNamespace(
                session=SimpleNamespace(close=close),
                executor=SimpleNamespace(shutdown=shutdown),
            ),
        )
        await main._force_spotify_cleanup(spotify)
        await asyncio.sleep(0)
        self.assertTrue(listener.cancelled())
        close.assert_called_once_with()
        shutdown.assert_called_once_with(wait=False, cancel_futures=True)

    async def test_hanging_disconnect_is_bounded_and_reported(self):
        async def hanging_disconnect(**_kwargs):
            await asyncio.sleep(10)

        session = SimpleNamespace(
            guild_id=9,
            cleanup_task=None,
            connect_task=None,
            dummy_load=None,
            ffmpeg_sources=deque(),
            voice_client=SimpleNamespace(
                stop=Mock(), disconnect=hanging_disconnect, cleanup=Mock()
            ),
        )
        started = time.monotonic()

        with self.assertRaisesRegex(RuntimeError, "forced voice disconnect"):
            await main._force_session_cleanup(session, started + 0.05)

        self.assertLess(time.monotonic() - started, 0.5)
