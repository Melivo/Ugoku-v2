import asyncio
import os
import signal
import time
import unittest
from collections import deque
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import main


class ShutdownBudgetTests(unittest.IsolatedAsyncioTestCase):
    async def test_hanging_session_forces_full_cleanup_within_total_deadline(self):
        source = SimpleNamespace(cleanup=Mock())
        voice = SimpleNamespace(
            stop=Mock(),
            disconnect=AsyncMock(),
            cleanup=Mock(),
        )

        async def hanging_cleanup():
            await asyncio.sleep(10)

        session = SimpleNamespace(
            guild_id=77,
            clean_session=hanging_cleanup,
            cleanup_task=None,
            connect_task=None,
            dummy_load=None,
            ffmpeg_sources=deque([source]),
            voice_client=voice,
        )
        spotify_session_close = Mock()
        executor_shutdown = Mock()
        spotify = SimpleNamespace(
            close=AsyncMock(),
            listener_task=None,
            lp=SimpleNamespace(
                session=SimpleNamespace(close=spotify_session_close),
                executor=SimpleNamespace(shutdown=executor_shutdown),
            ),
        )
        original_sessions = dict(main.session_manager.server_sessions)
        main.session_manager.server_sessions.clear()
        main.session_manager.server_sessions[77] = session
        main.bot.spotify_sessions = spotify
        main.bot._ugoku_closing = False
        started = time.monotonic()

        try:
            with patch.object(main, "HEALTH_SHUTDOWN_BUDGET", 0.20), patch.object(
                main, "HEALTH_FORCE_CLEANUP_BUDGET", 0.10
            ), patch.object(main.health_monitor, "stop", new=AsyncMock()), patch.object(
                main, "close_http_session", new=AsyncMock()
            ), patch.object(main, "original_close", new=AsyncMock()) as client_close:
                await main.close_bot()
        finally:
            main.session_manager.server_sessions.clear()
            main.session_manager.server_sessions.update(original_sessions)
            if hasattr(main.bot, "spotify_sessions"):
                delattr(main.bot, "spotify_sessions")
            main.bot._ugoku_closing = False

        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 0.50)
        source.cleanup.assert_called_once_with()
        voice.stop.assert_called_once_with()
        voice.disconnect.assert_awaited_once_with(force=True)
        voice.cleanup.assert_called_once_with()
        spotify_session_close.assert_called_once_with()
        executor_shutdown.assert_called_once_with(wait=False, cancel_futures=True)
        client_close.assert_awaited_once_with()

    async def test_finish_by_cancels_an_awaitable_after_deadline(self):
        cancelled = asyncio.Event()

        async def blocked():
            try:
                await asyncio.sleep(10)
            finally:
                cancelled.set()

        result = await main._finish_by(
            blocked(), time.monotonic() + 0.02, "blocked-test"
        )
        await asyncio.sleep(0)
        self.assertFalse(result)
        self.assertTrue(cancelled.is_set())


class ShutdownSignalLifecycleTests(unittest.TestCase):
    def test_run_replaces_pycord_loop_stop_with_async_close(self):
        callbacks = []
        signal_handlers = {}
        shutdown_awaitable = object()
        shutdown_task = Mock(done=Mock(return_value=False))
        fake_loop = SimpleNamespace(
            call_soon=Mock(side_effect=callbacks.append),
            add_signal_handler=Mock(
                side_effect=lambda sig, callback: signal_handlers.__setitem__(
                    sig, callback
                )
            ),
            create_task=Mock(return_value=shutdown_task),
            stop=Mock(),
        )

        def pycord_run(_token):
            signal_handlers[signal.SIGINT] = fake_loop.stop
            signal_handlers[signal.SIGTERM] = fake_loop.stop
            for callback in callbacks:
                callback()
            signal_handlers[signal.SIGTERM]()

        close = Mock(return_value=shutdown_awaitable)
        with patch.object(main, "loop", fake_loop), patch.object(
            main.bot, "close", new=close
        ), patch.object(main.bot, "run", side_effect=pycord_run):
            main.run_bot()

        fake_loop.stop.assert_not_called()
        close.assert_called_once_with()
        fake_loop.create_task.assert_called_once_with(shutdown_awaitable)
