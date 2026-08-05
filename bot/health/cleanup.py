from __future__ import annotations

import asyncio
import logging
import subprocess
import time
from typing import Any, Callable


logger = logging.getLogger(__name__)


def _child_process(resource: Any) -> Any | None:
    for attribute in ("_process", "process", "_proc"):
        process = getattr(resource, attribute, None)
        if process is not None and callable(getattr(process, "wait", None)):
            return process
    return None


async def _kill_and_wait(process: Any, deadline: float, label: str) -> None:
    poll = getattr(process, "poll", None)
    if not callable(poll) or poll() is None:
        kill = getattr(process, "kill", None)
        if not callable(kill):
            raise RuntimeError(f"{label} child process cannot be killed")
        kill()

    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(f"{label} child-process wait exceeded its deadline")
    try:
        await asyncio.wait_for(
            asyncio.to_thread(process.wait, timeout=remaining),
            timeout=remaining,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"{label} child process did not exit after kill"
        ) from exc


async def cleanup_with_deadline(
    resource: Any,
    cleanup: Callable[[], Any],
    deadline: float,
    label: str,
) -> None:
    """Run blocking cleanup and forcibly reap its child before the deadline."""
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError(f"{label} cleanup started after its deadline")

    process = _child_process(resource)
    force_reserve = min(0.25, remaining / 2) if process is not None else 0.0
    task = asyncio.create_task(asyncio.to_thread(cleanup))
    done, _ = await asyncio.wait(
        {task}, timeout=max(0.0, remaining - force_reserve)
    )
    if task in done:
        task.result()
        if process is not None:
            # Some cleanup implementations return without terminating their
            # child. Verify, kill when needed, and always wait to reap it.
            await _kill_and_wait(process, deadline, label)
        return

    if process is not None:
        await _kill_and_wait(process, deadline, label)
        remaining = max(0.0, deadline - time.monotonic())
        done, _ = await asyncio.wait({task}, timeout=remaining)
        if task in done:
            task.result()
            return

    task.cancel()
    logger.error("%s cleanup exceeded its deadline", label)
    raise TimeoutError(f"{label} cleanup exceeded its deadline")
