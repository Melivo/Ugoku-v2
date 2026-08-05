import asyncio
import logging
import os
import signal
import time
import discord

from config import (
    COMMANDS_FOLDER,
    SPOTIFY_API_ENABLED,
    GEMINI_ENABLED,
    PINECONE_INDEX_NAME,
    DEEZER_ENABLED,
    TEMP_FOLDER,
    HEALTH_FORCE_CLEANUP_BUDGET,
    HEALTH_MONITOR_ENABLED,
    HEALTH_SLA_BOOT_READY_S,
    HEALTH_SHUTDOWN_BUDGET,
)
from bot.health import HealthMonitor
from bot.health.cleanup import cleanup_with_deadline
from bot.misc.quickstart_view import QuickstartView
from bot.utils import cleanup_cache
from bot.vocal.spotify import SpotifySessions, Spotify
from bot.vocal.session_manager import session_manager
from bot.http_client import init_http_session, close_http_session




if GEMINI_ENABLED:
    from bot.chatbot.vector_recall import memory
if DEEZER_ENABLED:
    from deezer_decryption.api import Deezer

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Init bot
intents = discord.Intents.default()
intents.message_content = True
loop = asyncio.get_event_loop()
bot = discord.Bot(intents=intents, loop=loop)
original_close = bot.close
health_monitor = HealthMonitor(bot)
bot.health_monitor = health_monitor


async def _finish_by(awaitable, deadline: float, label: str) -> bool:
    """Wait without allowing cancellation-resistant work to exceed a deadline."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        if asyncio.iscoroutine(awaitable):
            awaitable.close()
        elif hasattr(awaitable, "cancel"):
            awaitable.cancel()
        return False
    task = asyncio.ensure_future(awaitable)
    done, _ = await asyncio.wait({task}, timeout=remaining)
    if task not in done:
        task.cancel()
        logging.warning("Shutdown step exceeded its deadline: %s", label)
        return False
    try:
        task.result()
        return True
    except asyncio.CancelledError:
        return True
    except Exception:
        logging.exception("Shutdown step failed: %s", label)
        return False


async def _force_session_cleanup(session, deadline: float | None = None) -> None:
    deadline = deadline or (time.monotonic() + HEALTH_FORCE_CLEANUP_BUDGET)
    errors = []
    for task_name in ("cleanup_task", "connect_task", "dummy_load"):
        task = getattr(session, task_name, None)
        if task and not task.done():
            task.cancel()

    sources = getattr(session, "ffmpeg_sources", None)
    source_cleanup = []
    if sources is not None:
        for source in list(sources):
            cleanup = getattr(source, "cleanup", None)
            if callable(cleanup):
                async def cleanup_source(source=source, cleanup=cleanup) -> None:
                    await cleanup_with_deadline(
                        source, cleanup, deadline, "FFmpeg source"
                    )
                    try:
                        sources.remove(source)
                    except ValueError:
                        pass

                source_cleanup.append(cleanup_source())

    voice_client = getattr(session, "voice_client", None)
    if voice_client is not None:
        stop = getattr(voice_client, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception as exc:
                logging.exception("Forced voice stop failed")
                errors.append(exc)
        disconnect = getattr(voice_client, "disconnect", None)
        if callable(disconnect):
            async def disconnect_voice_client() -> None:
                try:
                    await disconnect(force=True)
                except TypeError:
                    await disconnect()

            if not await _finish_by(
                disconnect_voice_client(), deadline, "forced voice disconnect"
            ):
                errors.append(TimeoutError("forced voice disconnect failed"))
        cleanup = getattr(voice_client, "cleanup", None)
        if callable(cleanup):
            source_cleanup.append(
                cleanup_with_deadline(
                    voice_client, cleanup, deadline, "voice client"
                )
            )

    if source_cleanup:
        results = await asyncio.gather(*source_cleanup, return_exceptions=True)
        errors.extend(result for result in results if isinstance(result, BaseException))
    if errors:
        raise RuntimeError(
            "; ".join(f"{type(error).__name__}: {error}" for error in errors)
        )
    guild_id = getattr(session, "guild_id", None)
    if session_manager.server_sessions.get(guild_id) is session:
        session_manager.server_sessions.pop(guild_id, None)


async def _force_spotify_cleanup(
    spotify_sessions, deadline: float | None = None
) -> None:
    deadline = deadline or (time.monotonic() + HEALTH_FORCE_CLEANUP_BUDGET)
    if spotify_sessions is None:
        return
    listener_task = getattr(spotify_sessions, "listener_task", None)
    if listener_task and not listener_task.done():
        listener_task.cancel()

    librespot = getattr(spotify_sessions, "lp", None)
    librespot_session = getattr(librespot, "session", None)
    close = getattr(librespot_session, "close", None)
    if callable(close):
        await cleanup_with_deadline(
            librespot, close, deadline, "Librespot session"
        )
    executor = getattr(librespot, "executor", None)
    shutdown = getattr(executor, "shutdown", None)
    if callable(shutdown):
        await asyncio.to_thread(shutdown, wait=False, cancel_futures=True)


async def _force_cleanup(
    sessions, spotify_sessions, deadline: float | None = None
) -> None:
    deadline = deadline or (time.monotonic() + HEALTH_FORCE_CLEANUP_BUDGET)
    results = await asyncio.gather(
        *(_force_session_cleanup(session, deadline) for session in sessions),
        _force_spotify_cleanup(spotify_sessions, deadline),
        close_http_session(),
        return_exceptions=True,
    )
    errors = [result for result in results if isinstance(result, BaseException)]
    for error in errors:
        logging.error(
            "Forced cleanup failed: %s: %s", type(error).__name__, error
        )
    if errors:
        raise RuntimeError(f"{len(errors)} forced cleanup step(s) failed")


async def close_bot() -> None:
    if getattr(bot, "_ugoku_closing", False):
        return
    bot._ugoku_closing = True
    deadline = time.monotonic() + HEALTH_SHUTDOWN_BUDGET
    force_budget = min(HEALTH_FORCE_CLEANUP_BUDGET, HEALTH_SHUTDOWN_BUDGET)
    graceful_deadline = deadline - force_budget
    sessions = list(session_manager.server_sessions.values())
    spotify_sessions = getattr(bot, "spotify_sessions", None)
    force_required = False

    if HEALTH_MONITOR_ENABLED:
        force_required |= not await _finish_by(
            health_monitor.stop(), graceful_deadline, "health monitor"
        )
    for session in sessions:
        force_required |= not await _finish_by(
            session.clean_session(), graceful_deadline, "server session"
        )

    cache_cleanup_task = getattr(bot, "cache_cleanup_task", None)
    if cache_cleanup_task and not cache_cleanup_task.done():
        cache_cleanup_task.cancel()
        force_required |= not await _finish_by(
            cache_cleanup_task, graceful_deadline, "cache cleanup task"
        )

    deezer_refresh_task = getattr(bot, "deezer_refresh_task", None)
    if deezer_refresh_task and not deezer_refresh_task.done():
        deezer_refresh_task.cancel()
        force_required |= not await _finish_by(
            deezer_refresh_task, graceful_deadline, "Deezer refresh task"
        )
    deezer = getattr(bot, "deezer", None)
    deezer_session = getattr(deezer, "session", None)
    deezer_close = getattr(deezer_session, "aclose", None)
    if callable(deezer_close):
        force_required |= not await _finish_by(
            deezer_close(), graceful_deadline, "Deezer session"
        )

    if spotify_sessions:
        force_required |= not await _finish_by(
            spotify_sessions.close(), graceful_deadline, "Spotify sessions"
        )
    force_required |= not await _finish_by(
        close_http_session(), graceful_deadline, "HTTP session"
    )

    if force_required or time.monotonic() >= graceful_deadline:
        # Keep a small slice of the force budget for py-cord's own close path.
        final_close_reserve = min(0.5, max(0.05, force_budget / 8))
        force_deadline = max(time.monotonic(), deadline - final_close_reserve)
        await _finish_by(
            _force_cleanup(sessions, spotify_sessions, force_deadline),
            force_deadline,
            "forced resource cleanup",
        )

    await _finish_by(original_close(), deadline, "Discord client")


bot.close = close_bot


def _install_shutdown_signal_handlers() -> None:
    """Let the async close lifecycle finish before py-cord stops its loop."""
    shutdown_task = None

    def request_shutdown() -> None:
        nonlocal shutdown_task
        if shutdown_task is None or shutdown_task.done():
            shutdown_task = loop.create_task(bot.close())

    try:
        loop.add_signal_handler(signal.SIGINT, request_shutdown)
        loop.add_signal_handler(signal.SIGTERM, request_shutdown)
    except (NotImplementedError, RuntimeError):
        pass


def run_bot() -> None:
    # Pycord's run() installs loop.stop signal handlers first. Replacing them
    # on the first loop iteration keeps the loop alive until close_bot finishes.
    loop.call_soon(_install_shutdown_signal_handlers)
    bot.run(BOT_TOKEN)


@bot.event
async def on_ready() -> None:
    if getattr(bot, "_ugoku_initialized", False) or getattr(
        bot, "_ugoku_initializing", False
    ):
        return
    bot._ugoku_initializing = True
    spotify_sessions = None
    spotify = None
    deezer = None
    deezer_refresh_task = None
    http_initialized = False
    health_started = False
    try:
        # Bound every operation that must finish before HealthMonitor emits
        # READY=1. systemd enforces the same hard startup deadline.
        async with asyncio.timeout(HEALTH_SLA_BOOT_READY_S):
            # Cache
            TEMP_FOLDER.mkdir(parents=True, exist_ok=True)
            await init_http_session()
            http_initialized = True

            activity = discord.Activity(
                type=discord.ActivityType.listening, name="/help for usage !"
            )
            if SPOTIFY_API_ENABLED:
                spotify_sessions = SpotifySessions()
                spotify = Spotify(spotify_sessions)

                if DEEZER_ENABLED:
                    deezer = Deezer()

            async with asyncio.TaskGroup() as group:
                group.create_task(bot.change_presence(activity=activity))
                if spotify_sessions is not None:
                    group.create_task(spotify_sessions.init_spotify())
                if deezer is not None:
                    group.create_task(deezer.setup(create_refresh_task=False))
                if GEMINI_ENABLED:
                    group.create_task(memory.init_pinecone(PINECONE_INDEX_NAME))

            if spotify_sessions is not None:
                bot.spotify_sessions = spotify_sessions
                bot.spotify = spotify
            if deezer is not None:
                bot.deezer = deezer

            if HEALTH_MONITOR_ENABLED:
                await health_monitor.start()
                health_started = True

        if deezer is not None:
            deezer_refresh_task = asyncio.create_task(deezer.refresh_deezer())
            bot.deezer_refresh_task = deezer_refresh_task

        cache_cleanup_task = getattr(bot, "cache_cleanup_task", None)
        if cache_cleanup_task is None or cache_cleanup_task.done():
            bot.cache_cleanup_task = asyncio.create_task(clean_cache_task())

        bot._ugoku_initialized = True
        # Party !
        logging.info(f"{bot.user} is running !")
    except BaseException:
        rollback = []
        if health_started:
            rollback.append(health_monitor.stop())
        if spotify_sessions is not None:
            rollback.append(spotify_sessions.close())
        if http_initialized:
            rollback.append(close_http_session())
        if deezer_refresh_task is not None:
            deezer_refresh_task.cancel()
            rollback.append(deezer_refresh_task)
        deezer_session = getattr(deezer, "session", None)
        deezer_close = getattr(deezer_session, "aclose", None)
        if callable(deezer_close):
            rollback.append(deezer_close())
        if rollback:
            results = await asyncio.gather(*rollback, return_exceptions=True)
            for error in results:
                if isinstance(error, BaseException):
                    logging.error(
                        "Initialization rollback failed: %s: %s",
                        type(error).__name__,
                        error,
                    )
        if spotify_sessions is not None and getattr(
            bot, "spotify_sessions", None
        ) is spotify_sessions:
            del bot.spotify_sessions
        if spotify is not None and getattr(bot, "spotify", None) is spotify:
            del bot.spotify
        if deezer is not None and getattr(bot, "deezer", None) is deezer:
            del bot.deezer
        if deezer_refresh_task is not None and getattr(
            bot, "deezer_refresh_task", None
        ) is deezer_refresh_task:
            del bot.deezer_refresh_task
        raise
    finally:
        bot._ugoku_initializing = False


@bot.event
async def on_guild_join(guild: discord.Guild) -> None:
    channel = guild.system_channel
    if channel is None:
        for c in guild.text_channels:
            if c.permissions_for(guild.me).send_messages:
                channel = c
                break
    if channel is not None:
        quickstart_view = QuickstartView(timeout=None)
        await quickstart_view.display(respond_func=channel.send)


@bot.event
async def on_close() -> None:
    await close_http_session()


async def clean_cache_task() -> None:
    while True:
        await cleanup_cache()
        await asyncio.sleep(60)


if __name__ == "__main__":
    for filepath in COMMANDS_FOLDER.rglob("*.py"):
        relative_path = filepath.relative_to(COMMANDS_FOLDER).with_suffix("")
        module_name = f"commands.{relative_path.as_posix().replace('/', '.')}"
        logging.info(f"Loading {module_name}")
        bot.load_extension(module_name)

    run_bot()
