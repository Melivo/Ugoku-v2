import asyncio
from builtins import ExceptionGroup
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

import main
from bot.vocal import spotify as spotify_module


class MainInitializationTests(unittest.IsolatedAsyncioTestCase):
    async def test_boot_ready_initialization_times_out_and_rolls_back(self):
        original_initialized = getattr(main.bot, "_ugoku_initialized", None)
        original_initializing = getattr(main.bot, "_ugoku_initializing", None)
        main.bot._ugoku_initialized = False
        main.bot._ugoku_initializing = False

        async def blocked_spotify_init():
            await asyncio.Event().wait()

        fake_sessions = SimpleNamespace(
            init_spotify=blocked_spotify_init,
            close=AsyncMock(),
        )

        try:
            with tempfile.TemporaryDirectory() as directory, patch.object(
                main, "TEMP_FOLDER", Path(directory)
            ), patch.object(main, "SPOTIFY_API_ENABLED", True), patch.object(
                main, "DEEZER_ENABLED", False
            ), patch.object(main, "GEMINI_ENABLED", False), patch.object(
                main, "HEALTH_MONITOR_ENABLED", True
            ), patch.object(main, "HEALTH_SLA_BOOT_READY_S", 0.05), patch.object(
                main, "init_http_session", new=AsyncMock()
            ), patch.object(
                main, "close_http_session", new=AsyncMock()
            ) as close_http, patch.object(
                main, "SpotifySessions", return_value=fake_sessions
            ), patch.object(
                main, "Spotify", return_value=object()
            ), patch.object(
                main.bot, "change_presence", new=AsyncMock()
            ), patch.object(
                main.health_monitor, "start", new=AsyncMock()
            ) as health_start:
                started = asyncio.get_running_loop().time()
                with self.assertRaises(TimeoutError):
                    await main.on_ready()
                elapsed = asyncio.get_running_loop().time() - started

            self.assertLess(elapsed, 0.5)
            health_start.assert_not_awaited()
            fake_sessions.close.assert_awaited_once_with()
            close_http.assert_awaited_once_with()
            self.assertFalse(main.bot._ugoku_initialized)
            self.assertFalse(main.bot._ugoku_initializing)
        finally:
            if original_initialized is None:
                delattr(main.bot, "_ugoku_initialized")
            else:
                main.bot._ugoku_initialized = original_initialized
            if original_initializing is None:
                delattr(main.bot, "_ugoku_initializing")
            else:
                main.bot._ugoku_initializing = original_initializing

    async def test_failed_initialization_remains_retryable_and_sets_guard_after_success(self):
        original_initialized = getattr(main.bot, "_ugoku_initialized", None)
        original_initializing = getattr(main.bot, "_ugoku_initializing", None)
        original_cache_task = getattr(main.bot, "cache_cleanup_task", None)
        main.bot._ugoku_initialized = False
        main.bot._ugoku_initializing = False
        main.bot.cache_cleanup_task = None
        parked = asyncio.Event()

        async def parked_cache_cleanup():
            await parked.wait()

        try:
            with tempfile.TemporaryDirectory() as directory, patch.object(
                main, "TEMP_FOLDER", Path(directory)
            ), patch.object(main, "SPOTIFY_API_ENABLED", False), patch.object(
                main, "GEMINI_ENABLED", False
            ), patch.object(main, "HEALTH_MONITOR_ENABLED", False), patch.object(
                main,
                "init_http_session",
                new=AsyncMock(side_effect=[RuntimeError("transient"), None]),
            ) as init_http, patch.object(
                main.bot, "change_presence", new=AsyncMock()
            ), patch.object(main, "clean_cache_task", side_effect=parked_cache_cleanup):
                with self.assertRaisesRegex(RuntimeError, "transient"):
                    await main.on_ready()
                self.assertFalse(main.bot._ugoku_initialized)
                self.assertFalse(main.bot._ugoku_initializing)

                await main.on_ready()

                self.assertTrue(main.bot._ugoku_initialized)
                self.assertFalse(main.bot._ugoku_initializing)
                self.assertEqual(init_http.await_count, 2)
        finally:
            cache_task = getattr(main.bot, "cache_cleanup_task", None)
            if cache_task is not None and cache_task is not original_cache_task:
                cache_task.cancel()
                await asyncio.gather(cache_task, return_exceptions=True)
            if original_initialized is None:
                delattr(main.bot, "_ugoku_initialized")
            else:
                main.bot._ugoku_initialized = original_initialized
            if original_initializing is None:
                delattr(main.bot, "_ugoku_initializing")
            else:
                main.bot._ugoku_initializing = original_initializing
            if original_cache_task is None:
                if hasattr(main.bot, "cache_cleanup_task"):
                    delattr(main.bot, "cache_cleanup_task")
            else:
                main.bot.cache_cleanup_task = original_cache_task

    async def test_partial_parallel_init_cancels_and_rolls_back_spotify(self):
        original_initialized = getattr(main.bot, "_ugoku_initialized", None)
        original_initializing = getattr(main.bot, "_ugoku_initializing", None)
        original_spotify_sessions = getattr(main.bot, "spotify_sessions", None)
        original_spotify = getattr(main.bot, "spotify", None)
        main.bot._ugoku_initialized = False
        main.bot._ugoku_initializing = False
        spotify_started = asyncio.Event()
        spotify_cancelled = asyncio.Event()

        async def init_spotify():
            spotify_started.set()
            try:
                await asyncio.Event().wait()
            finally:
                spotify_cancelled.set()

        fake_sessions = SimpleNamespace(
            init_spotify=init_spotify,
            close=AsyncMock(),
        )

        async def fail_presence(**_kwargs):
            await spotify_started.wait()
            raise RuntimeError("presence failed")

        try:
            with tempfile.TemporaryDirectory() as directory, patch.object(
                main, "TEMP_FOLDER", Path(directory)
            ), patch.object(main, "SPOTIFY_API_ENABLED", True), patch.object(
                main, "DEEZER_ENABLED", False
            ), patch.object(main, "GEMINI_ENABLED", False), patch.object(
                main, "HEALTH_MONITOR_ENABLED", False
            ), patch.object(main, "init_http_session", new=AsyncMock()), patch.object(
                main, "close_http_session", new=AsyncMock()
            ) as close_http, patch.object(
                main, "SpotifySessions", return_value=fake_sessions
            ), patch.object(
                main, "Spotify", return_value=object()
            ), patch.object(
                main.bot, "change_presence", side_effect=fail_presence
            ):
                with self.assertRaises(ExceptionGroup) as raised:
                    await main.on_ready()

            self.assertTrue(
                any(
                    isinstance(error, RuntimeError)
                    and str(error) == "presence failed"
                    for error in raised.exception.exceptions
                )
            )
            self.assertTrue(spotify_cancelled.is_set())
            fake_sessions.close.assert_awaited_once_with()
            close_http.assert_awaited_once_with()
            self.assertFalse(main.bot._ugoku_initialized)
            self.assertFalse(main.bot._ugoku_initializing)
            self.assertIsNot(getattr(main.bot, "spotify_sessions", None), fake_sessions)
        finally:
            if original_initialized is None:
                delattr(main.bot, "_ugoku_initialized")
            else:
                main.bot._ugoku_initialized = original_initialized
            if original_initializing is None:
                delattr(main.bot, "_ugoku_initializing")
            else:
                main.bot._ugoku_initializing = original_initializing
            if original_spotify_sessions is None:
                if hasattr(main.bot, "spotify_sessions"):
                    delattr(main.bot, "spotify_sessions")
            else:
                main.bot.spotify_sessions = original_spotify_sessions
            if original_spotify is None:
                if hasattr(main.bot, "spotify"):
                    delattr(main.bot, "spotify")
            else:
                main.bot.spotify = original_spotify

    async def test_cancelled_spotify_init_closes_partial_librespot_resources(self):
        create_started = asyncio.Event()

        async def create_session():
            create_started.set()
            await asyncio.Event().wait()

        fake_librespot = SimpleNamespace(
            create_session=create_session,
            listen_to_session=AsyncMock(),
            close_session=AsyncMock(),
            executor=SimpleNamespace(shutdown=Mock()),
        )
        sessions = spotify_module.SpotifySessions()

        with patch.object(spotify_module, "SPOTIFY_ENABLED", True), patch.object(
            spotify_module, "SPOTIFY_API_ENABLED", False
        ), patch.object(spotify_module, "Librespot", return_value=fake_librespot):
            init_task = asyncio.create_task(sessions.init_spotify())
            await create_started.wait()
            init_task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await init_task

        fake_librespot.close_session.assert_awaited_once_with()
        fake_librespot.executor.shutdown.assert_called_once_with(
            wait=False, cancel_futures=True
        )
        self.assertIsNone(sessions.lp)
        self.assertIsNone(sessions.listener_task)

    async def test_failed_spotify_init_is_single_attempt_and_propagates(self):
        fake_librespot = SimpleNamespace(
            create_session=AsyncMock(side_effect=RuntimeError("spotify unavailable")),
            listen_to_session=AsyncMock(),
            close_session=AsyncMock(),
            executor=SimpleNamespace(shutdown=Mock()),
        )
        sessions = spotify_module.SpotifySessions()

        with patch.object(spotify_module, "SPOTIFY_ENABLED", True), patch.object(
            spotify_module, "SPOTIFY_API_ENABLED", False
        ), patch.object(
            spotify_module, "Librespot", return_value=fake_librespot
        ) as librespot_factory:
            started = asyncio.get_running_loop().time()
            with self.assertRaisesRegex(RuntimeError, "spotify unavailable"):
                await sessions.init_spotify()
            elapsed = asyncio.get_running_loop().time() - started

        self.assertLess(elapsed, 0.5)
        librespot_factory.assert_called_once_with()
        fake_librespot.create_session.assert_awaited_once_with()
        fake_librespot.close_session.assert_awaited_once_with()
        fake_librespot.executor.shutdown.assert_called_once_with(
            wait=False, cancel_futures=True
        )
        self.assertIsNone(sessions.lp)

    async def test_spotify_startup_calls_single_attempt_boundary_once(self):
        sessions = spotify_module.SpotifySessions()

        with patch.object(
            sessions,
            "_init_spotify_once",
            new=AsyncMock(side_effect=RuntimeError("permanent failure")),
        ) as initialize_once, patch.object(
            sessions, "close", new=AsyncMock()
        ) as close:
            with self.assertRaisesRegex(RuntimeError, "permanent failure"):
                await sessions.init_spotify()

        initialize_once.assert_awaited_once_with()
        close.assert_awaited_once_with()
