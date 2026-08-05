from __future__ import annotations

import asyncio
from dataclasses import dataclass
import inspect
import logging
import time
from typing import Any

import discord
from librespot.metadata import TrackId

from config import (
    DEFAULT_AUDIO_BITRATE,
    HEALTH_AUDIO_PROBE_BYTES,
    HEALTH_AUDIO_PROBE_TIMEOUT,
    HEALTH_AUDIO_PROBE_TRACK_ID,
    SPOTIFY_ENABLED,
)
from bot.health.cleanup import cleanup_with_deadline


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AudioProbeResult:
    ok: bool | None
    service: str
    duration_s: float
    bytes_read: int
    error: str | None


async def probe_audio(
    bot: Any,
    *,
    timeout: float = HEALTH_AUDIO_PROBE_TIMEOUT,
    bytes_to_read: int = HEALTH_AUDIO_PROBE_BYTES,
    track_id: str | None = HEALTH_AUDIO_PROBE_TRACK_ID,
) -> AudioProbeResult:
    """Probe Librespot -> FFmpegOpusAudio without voice or user queue access."""
    started = time.monotonic()
    spotify_sessions = getattr(bot, "spotify_sessions", None)
    librespot = getattr(spotify_sessions, "lp", None)
    session_marker = getattr(librespot, "session", librespot)
    if not SPOTIFY_ENABLED:
        return AudioProbeResult(
            ok=None,
            service="n/a",
            duration_s=time.monotonic() - started,
            bytes_read=0,
            error="spotify disabled",
        )
    if librespot is None or session_marker is None:
        return AudioProbeResult(
            ok=False,
            service="spotify",
            duration_s=time.monotonic() - started,
            bytes_read=0,
            error="Spotify audio session unavailable",
        )
    if timeout <= 0 or bytes_to_read <= 0:
        return AudioProbeResult(
            ok=False,
            service="spotify",
            duration_s=time.monotonic() - started,
            bytes_read=0,
            error="timeout and bytes_to_read must be positive",
        )

    stream = None
    source: discord.FFmpegOpusAudio | None = None
    read_count = 0
    error: str | None = None
    cleanup_errors: list[str] = []
    deadline = started + timeout
    cleanup_reserve = min(2.0, max(0.05, timeout * 0.2))
    try:
        async with asyncio.timeout(max(0.001, timeout - cleanup_reserve)):
            resolved_track = await _resolve_track_id(spotify_sessions, track_id)
            if resolved_track is None:
                return AudioProbeResult(
                    ok=False,
                    service="spotify",
                    duration_s=time.monotonic() - started,
                    bytes_read=0,
                    error="no configured or discoverable Spotify probe track",
                )
            stream = await _maybe_await(librespot.get_stream(resolved_track))
            source = await asyncio.to_thread(
                discord.FFmpegOpusAudio,
                stream,
                pipe=True,
                bitrate=DEFAULT_AUDIO_BITRATE,
            )
            while read_count < bytes_to_read:
                packet = await asyncio.to_thread(source.read)
                if not packet:
                    break
                read_count += len(packet)
    except TimeoutError:
        error = f"audio probe timed out after {timeout:.3f}s"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if source is not None:
            cleanup_error = await _cleanup_by(
                source, source.cleanup, deadline, "FFmpeg source"
            )
            if cleanup_error:
                cleanup_errors.append(cleanup_error)
        if stream is not None:
            close = getattr(stream, "close", None)
            if callable(close):
                cleanup_error = await _cleanup_by(stream, close, deadline, "audio stream")
                if cleanup_error:
                    cleanup_errors.append(cleanup_error)

    if cleanup_errors:
        cleanup_message = "; ".join(cleanup_errors)
        error = f"{error}; {cleanup_message}" if error else cleanup_message

    duration = time.monotonic() - started
    if error is not None:
        return AudioProbeResult(
            ok=False,
            service="spotify",
            duration_s=duration,
            bytes_read=0,
            error=error,
        )
    if read_count < 1:
        return AudioProbeResult(
            ok=False,
            service="spotify",
            duration_s=duration,
            bytes_read=0,
            error="FFmpeg produced no Opus bytes",
        )
    return AudioProbeResult(
        ok=True,
        service="spotify",
        duration_s=duration,
        bytes_read=read_count,
        error=None,
    )


async def _resolve_track_id(
    spotify_sessions: Any, track_id: str | None
) -> TrackId | Any | None:
    if track_id:
        if not isinstance(track_id, str):
            return track_id
        uri = track_id if track_id.startswith("spotify:track:") else f"spotify:track:{track_id}"
        return await asyncio.to_thread(TrackId.from_uri, uri)

    spotify_api = getattr(spotify_sessions, "sp", None)
    search = getattr(spotify_api, "search", None)
    if not callable(search):
        return None
    result = await asyncio.to_thread(search, q="*", type="track", limit=1)
    result = await _maybe_await(result)
    items = ((result or {}).get("tracks") or {}).get("items") or []
    first_id = items[0].get("id") if items and isinstance(items[0], dict) else None
    if not first_id:
        return None
    return await asyncio.to_thread(TrackId.from_uri, f"spotify:track:{first_id}")


async def _maybe_await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


async def _cleanup_by(
    resource: Any, function: Any, deadline: float, label: str
) -> str | None:
    try:
        await cleanup_with_deadline(resource, function, deadline, label)
        return None
    except Exception as exc:
        logger.exception("%s cleanup failed", label)
        return f"{label} cleanup failed: {type(exc).__name__}: {exc}"
