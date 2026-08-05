from __future__ import annotations

import asyncio
from dataclasses import asdict
import json
import logging
import os
from pathlib import Path
import socket
import tempfile
import time
from typing import Any
from uuid import uuid4

from bot.health.audio_probe import AudioProbeResult, probe_audio
from bot.vocal.session_manager import session_manager
from config import (
    HEALTH_AUDIO_PROBE_COOLDOWN,
    HEALTH_FFMPEG_ORPHAN_THRESHOLD,
    HEALTH_LIBRESPOT_STALE_S,
    HEALTH_MONITOR_INTERVAL,
    HEALTH_STATE_FILE,
    HEALTH_STATE_MODE,
    HEALTH_VOICE_CONNECT_STUCK_S,
    SPOTIFY_ENABLED,
)


logger = logging.getLogger(__name__)


class HealthMonitor:
    """Publish bot observations without owning incidents, alerts, or restarts."""

    def __init__(self, bot: Any) -> None:
        self.bot = bot
        self.boot_id = str(uuid4())
        self._boot_monotonic = time.monotonic()
        self._gateway_state_changed = self._boot_monotonic
        self._gateway_was_ready: bool | None = None
        self._task: asyncio.Task[None] | None = None
        self._ready_notified = False
        self._last_tick_monotonic = self._boot_monotonic
        self._last_loop_lag_ms = 0.0
        self._readiness: dict[str, Any] = {
            "slash_ready": False,
            "audio_ready": None,
            "last_check_monotonic": None,
        }
        self._audio_probe_lock = asyncio.Lock()
        self._last_audio_probe: AudioProbeResult | None = None
        self._last_audio_probe_monotonic: float | None = None
        self._last_audio_success_monotonic: float | None = None
        self._listener_first_seen_monotonic: float | None = None
        self._listener_was_seen = False
        self._connect_first_seen: dict[int, float] = {}
        self._blocked_reason: str | None = None
        self._blocked_since_monotonic: float | None = None

    async def start(self) -> None:
        """Publish one valid snapshot before READY and start one monitor task."""
        if self._task is not None and not self._task.done():
            return
        if not self._ready_notified:
            await self.run_readiness_probe()
            state = await self.write_state()
            if not self._valid_initial_snapshot(state):
                raise RuntimeError("health monitor produced an invalid initial snapshot")
            self._sd_notify("READY=1")
            self._ready_notified = True
        self._task = asyncio.create_task(
            self._run(), name="ugoku-health-monitor"
        )

    async def stop(self) -> None:
        task = self._task
        self._task = None
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    def _sd_notify(self, state: str) -> None:
        """Send one systemd notification using only the Python standard library."""
        notify_socket = os.environ.get("NOTIFY_SOCKET")
        if not notify_socket:
            logger.debug("NOTIFY_SOCKET is unset; sd_notify is a no-op")
            return

        address: str | bytes = notify_socket
        if notify_socket.startswith("@"):
            address = b"\0" + notify_socket[1:].encode()
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
                client.connect(address)
                client.sendall(state.encode())
        except OSError as exc:
            logger.warning("Unable to send systemd notification %s: %s", state, exc)

    async def _run(self) -> None:
        next_tick = time.monotonic()
        while True:
            now = time.monotonic()
            self._last_loop_lag_ms = max(0.0, (now - next_tick) * 1000)
            self._last_tick_monotonic = now
            try:
                await self.run_readiness_probe()
                await self.write_state()
                self._sd_notify("WATCHDOG=1")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Health monitor tick failed")

            next_tick += HEALTH_MONITOR_INTERVAL
            delay = next_tick - time.monotonic()
            if delay <= 0:
                next_tick = time.monotonic()
                delay = 0
            await asyncio.sleep(delay)

    async def run_readiness_probe(self) -> dict[str, Any]:
        """Check slash registration and production audio without touching queues."""
        slash_ready = self._slash_command_ready()
        audio_result = await self._get_audio_probe_result()
        checked_at = time.monotonic()
        self._readiness = {
            "slash_ready": slash_ready,
            "audio_ready": audio_result.ok,
            "last_check_monotonic": checked_at,
        }
        return {
            **self._readiness,
            "audio_probe": asdict(audio_result),
        }

    async def _get_audio_probe_result(self) -> AudioProbeResult:
        async with self._audio_probe_lock:
            now = time.monotonic()
            if (
                self._last_audio_probe is not None
                and self._last_audio_probe_monotonic is not None
                and now - self._last_audio_probe_monotonic
                < HEALTH_AUDIO_PROBE_COOLDOWN
            ):
                return self._last_audio_probe

            result = await probe_audio(self.bot)
            self._last_audio_probe = result
            self._last_audio_probe_monotonic = time.monotonic()
            if result.ok is True:
                self._last_audio_success_monotonic = self._last_audio_probe_monotonic
            return result

    def _slash_command_ready(self) -> bool:
        if not self._bot_bool("is_ready"):
            return False

        command_sources_present = False
        for attribute in ("application_commands", "pending_application_commands"):
            commands = getattr(self.bot, attribute, None)
            if commands is None:
                continue
            command_sources_present = True
            values = commands.values() if isinstance(commands, dict) else commands
            if any(getattr(command, "name", None) == "health" for command in values):
                return True

        getter = getattr(self.bot, "get_application_command", None)
        if callable(getter):
            command_sources_present = True
            try:
                if getter("health") is not None:
                    return True
            except (LookupError, TypeError):
                pass

        # Minimal bot doubles without command registries remain compatible; real
        # py-cord Bot instances always expose one of the sources above.
        return not command_sources_present

    async def snapshot(self) -> dict[str, Any]:
        now_monotonic = time.monotonic()
        ready = self._bot_bool("is_ready")
        closed = self._gateway_closed()
        connected = self._gateway_connected(ready, closed)
        if self._gateway_was_ready is None or ready != self._gateway_was_ready:
            self._gateway_state_changed = now_monotonic
            self._gateway_was_ready = ready

        latency = getattr(self.bot, "latency", None)
        latency_ms = None
        if isinstance(latency, (int, float)) and latency >= 0:
            latency_ms = float(latency) * 1000

        sessions = list(session_manager.server_sessions.values())
        guild_ids: list[int] = []
        playing = 0
        ffmpeg_orphans = 0
        stuck_connects = 0
        active_connect_ids: set[int] = set()

        for session in sessions:
            guild_id = getattr(session, "guild_id", None)
            if isinstance(guild_id, int):
                guild_ids.append(guild_id)

            voice_client = getattr(session, "voice_client", None)
            is_playing = self._object_bool(voice_client, "is_playing")
            is_paused = self._object_bool(voice_client, "is_paused")
            if is_playing:
                playing += 1
            source_active = is_playing or is_paused
            active_source = (
                getattr(voice_client, "source", None) if source_active else None
            )
            for source in list(getattr(session, "ffmpeg_sources", ())):
                if source is not active_source:
                    ffmpeg_orphans += 1

            connect_task = getattr(session, "connect_task", None)
            if connect_task is not None and not self._task_done(connect_task):
                task_id = id(connect_task)
                active_connect_ids.add(task_id)
                first_seen = getattr(
                    session,
                    "connect_started_monotonic",
                    self._connect_first_seen.setdefault(task_id, now_monotonic),
                )
                if now_monotonic - float(first_seen) > HEALTH_VOICE_CONNECT_STUCK_S:
                    stuck_connects += 1

        self._connect_first_seen = {
            task_id: started
            for task_id, started in self._connect_first_seen.items()
            if task_id in active_connect_ids
        }

        spotify = self._spotify_snapshot(now_monotonic)
        blocked_reason = None
        if stuck_connects:
            blocked_reason = "voice"
        elif ffmpeg_orphans > HEALTH_FFMPEG_ORPHAN_THRESHOLD:
            blocked_reason = "ffmpeg"
        elif spotify["listener_blocked"]:
            blocked_reason = "librespot"

        if blocked_reason is None:
            self._blocked_reason = None
            self._blocked_since_monotonic = None
        elif blocked_reason != self._blocked_reason:
            self._blocked_reason = blocked_reason
            self._blocked_since_monotonic = now_monotonic

        return {
            "pid": os.getpid(),
            "boot_id": self.boot_id,
            "timestamp": time.time(),
            "monotonic_now": now_monotonic,
            "uptime_s": max(0.0, now_monotonic - self._boot_monotonic),
            "gateway": {
                "connected": connected,
                "closed": closed,
                "ready": ready,
                "ready_age_s": max(
                    0.0, now_monotonic - self._gateway_state_changed
                ),
                "latency_ms": latency_ms,
            },
            "event_loop": {
                "last_tick_monotonic": self._last_tick_monotonic,
                "lag_ms": self._last_loop_lag_ms,
            },
            "readiness": dict(self._readiness),
            "sessions": {
                "count": len(sessions),
                "playing": playing,
                "guild_ids": sorted(guild_ids),
            },
            "spotify": {
                key: value
                for key, value in spotify.items()
                if key != "listener_blocked"
            },
            "ffmpeg": {"orphan_sources": ffmpeg_orphans},
            "voice": {"stuck_connects": stuck_connects},
            "resource_blocked": {
                "blocked": blocked_reason is not None,
                "reason": blocked_reason,
                "since_monotonic": self._blocked_since_monotonic,
            },
            "version": 1,
        }

    def _spotify_snapshot(self, now_monotonic: float) -> dict[str, Any]:
        if not SPOTIFY_ENABLED:
            return {
                "enabled": False,
                "session_alive": None,
                "listener_alive": None,
                "listener_last_beat_monotonic": None,
                "last_check_monotonic": self._readiness["last_check_monotonic"],
                "listener_blocked": False,
            }

        sessions = getattr(self.bot, "spotify_sessions", None)
        librespot = getattr(sessions, "lp", None) if sessions is not None else None
        listener_task = (
            getattr(sessions, "listener_task", None) if sessions is not None else None
        )
        session_alive = bool(librespot and getattr(librespot, "session", None))
        listener_alive = bool(listener_task and not self._task_done(listener_task))
        if listener_task is not None:
            self._listener_was_seen = True
            if self._listener_first_seen_monotonic is None:
                self._listener_first_seen_monotonic = now_monotonic
        last_beat = None
        if sessions is not None:
            last_beat = getattr(sessions, "listener_last_beat_monotonic", None)
        if last_beat is None and librespot is not None:
            last_beat = getattr(librespot, "listener_last_beat_monotonic", None)
        if last_beat is None and listener_task is not None:
            # The queue-isolated production decode is also a concrete Librespot
            # heartbeat when the legacy listener exposes no timestamp itself.
            last_beat = (
                self._last_audio_success_monotonic
                or self._listener_first_seen_monotonic
            )
        listener_stale = bool(
            listener_task is not None
            and last_beat is not None
            and now_monotonic - float(last_beat) > HEALTH_LIBRESPOT_STALE_S
        )
        listener_done = bool(
            (listener_task and self._task_done(listener_task))
            or (
                listener_task is None
                and self._listener_was_seen
                and session_alive
            )
        )
        return {
            "enabled": True,
            "session_alive": session_alive,
            "listener_alive": listener_alive,
            "listener_last_beat_monotonic": last_beat,
            "last_check_monotonic": self._readiness["last_check_monotonic"],
            "listener_blocked": listener_done or listener_stale,
        }

    async def write_state(self) -> dict[str, Any]:
        state = await self.snapshot()
        await asyncio.to_thread(self._atomic_write_json, HEALTH_STATE_FILE, state)
        return state

    def _valid_initial_snapshot(self, state: dict[str, Any]) -> bool:
        return bool(
            state.get("version") == 1
            and state.get("boot_id") == self.boot_id
            and isinstance(state.get("timestamp"), (int, float))
            and isinstance(state.get("gateway"), dict)
            and isinstance(state.get("readiness"), dict)
            and state["readiness"].get("last_check_monotonic") is not None
        )

    @staticmethod
    def _atomic_write_json(path: Path, state: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(state, temporary, separators=(",", ":"), sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.chmod(temporary_path, HEALTH_STATE_MODE)
            os.replace(temporary_path, path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink(missing_ok=True)

    def _gateway_closed(self) -> bool:
        if self._bot_bool("is_closed"):
            return True
        websocket = getattr(self.bot, "ws", None)
        return bool(websocket is not None and getattr(websocket, "closed", False))

    def _gateway_connected(self, ready: bool, closed: bool) -> bool:
        if closed:
            return False
        websocket = getattr(self.bot, "ws", None)
        if websocket is None:
            return ready
        open_state = getattr(websocket, "open", None)
        return bool(ready if open_state is None else open_state)

    def _bot_bool(self, attribute: str) -> bool:
        value = getattr(self.bot, attribute, False)
        try:
            return bool(value() if callable(value) else value)
        except Exception:
            return False

    @staticmethod
    def _object_bool(instance: Any, attribute: str) -> bool:
        if instance is None:
            return False
        value = getattr(instance, attribute, False)
        try:
            return bool(value() if callable(value) else value)
        except Exception:
            return False

    @staticmethod
    def _task_done(task: Any) -> bool:
        done = getattr(task, "done", None)
        try:
            return bool(done() if callable(done) else done)
        except Exception:
            return False
