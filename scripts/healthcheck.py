#!/usr/bin/env python3
"""External Ugoku health probe and the sole owner of incident runtime state."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (  # noqa: E402
    ADMIN_ALERT_WEBHOOK,
    HEALTH_ALERT_OUTBOX_FILE,
    HEALTH_ALERT_TIMEOUT,
    HEALTH_FAILURE_THRESHOLD,
    HEALTH_FAIL_COUNT_FILE,
    HEALTH_GATEWAY_LATENCY_THRESHOLD_MS,
    HEALTH_INCIDENT_FILE,
    HEALTH_LOOP_LAG_THRESHOLD_MS,
    HEALTH_READY_GRACE,
    HEALTH_SLA_RESTART_TRIGGER_S,
    HEALTH_STALE_THRESHOLD,
    HEALTH_STATE_FILE,
)


EXIT_OK = 0
EXIT_STALE = 2
EXIT_GATEWAY_DOWN = 3
EXIT_SPOTIFY_DOWN = 4
EXIT_EVENT_LOOP_LAG = 5
EXIT_RESOURCE_BLOCKED = 6
EXIT_SLASH_NOT_READY = 7
EXIT_AUDIO_NOT_READY = 8

INCIDENT_MODE = 0o640
OUTBOX_MODE = 0o640
FAIL_COUNT_MODE = 0o644
RESTART_COMMAND = [
    "sudo",
    "-n",
    "/bin/systemctl",
    "--no-block",
    "restart",
    "ugoku.service",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as source:
            value = json.load(source)
        return value if isinstance(value, dict) else None
    except (OSError, ValueError, TypeError):
        return None


def atomic_write(path: Path, content: str, mode: int) -> None:
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
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink(missing_ok=True)


def atomic_write_json(path: Path, value: dict[str, Any], mode: int) -> None:
    atomic_write(
        path,
        json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n",
        mode,
    )


@contextmanager
def incident_state_lock(lock_path: Path | None = None):
    """Serialize all incident transitions across Linux healthcheck processes."""
    path = lock_path or HEALTH_INCIDENT_FILE.with_name("incident.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR, INCIDENT_MODE)
    with os.fdopen(descriptor, "a+b", buffering=0) as lock_file:
        if os.name == "nt":
            import msvcrt

            lock_file.seek(0)
            if lock_file.read(1) == b"":
                lock_file.write(b"\0")
                lock_file.flush()
            lock_file.seek(0)
            msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                lock_file.seek(0)
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def read_failure_count() -> int:
    try:
        return max(0, int(HEALTH_FAIL_COUNT_FILE.read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        return 0


def write_failure_count(value: int) -> None:
    atomic_write(HEALTH_FAIL_COUNT_FILE, f"{max(0, value)}\n", FAIL_COUNT_MODE)


def read_outbox() -> dict[str, Any]:
    outbox = read_json(HEALTH_ALERT_OUTBOX_FILE)
    if outbox is None or not isinstance(outbox.get("events"), list):
        return {"version": 1, "events": []}
    return outbox


def _write_outbox_locked(outbox: dict[str, Any]) -> None:
    atomic_write_json(HEALTH_ALERT_OUTBOX_FILE, outbox, OUTBOX_MODE)


def _queue_alert_locked(kind: str, incident: dict[str, Any]) -> dict[str, Any]:
    """Persist one alert per incident/kind before attempting delivery."""
    outbox = read_outbox()
    for event in outbox["events"]:
        if (
            event.get("incident_id") == incident.get("incident_id")
            and event.get("kind") == kind
        ):
            return event

    from uuid import uuid4

    event = {
        "event_id": str(uuid4()),
        "incident_id": incident["incident_id"],
        "kind": kind,
        "incident": dict(incident),
        "created_at_wall": utc_now(),
        "attempts": 0,
        "last_attempt_at_wall": None,
        "delivered": False,
        "delivered_at_wall": None,
    }
    outbox["events"].append(event)
    _write_outbox_locked(outbox)
    return event


def _flush_outbox_locked() -> None:
    """Deliver pending alerts in creation order with durable retry metadata."""
    outbox = read_outbox()
    for event in outbox["events"]:
        if event.get("delivered") is True:
            continue
        event["attempts"] = max(0, int(event.get("attempts", 0))) + 1
        event["last_attempt_at_wall"] = utc_now()
        _write_outbox_locked(outbox)
        if not send_webhook(
            str(event["kind"]),
            dict(event["incident"]),
            event_id=str(event["event_id"]),
        ):
            # Preserve event ordering: RECOVERY must not overtake OUTAGE/RESTART.
            return
        event["delivered"] = True
        event["delivered_at_wall"] = utc_now()
        _write_outbox_locked(outbox)


def _ensure_incident_alerts_locked(incident: dict[str, Any]) -> None:
    _queue_alert_locked("OUTAGE", incident)
    if incident.get("restart_triggered") is True:
        _queue_alert_locked("RESTART", incident)


def evaluate_state(state_path: Path) -> dict[str, Any]:
    state = read_json(state_path)
    freshness_s: float | None = None
    try:
        freshness_s = max(0.0, time.time() - state_path.stat().st_mtime)
    except OSError:
        pass

    result: dict[str, Any] = {
        "status": "STALE",
        "exit_code": EXIT_STALE,
        "reason": "stale",
        "state_file": str(state_path),
        "freshness_s": freshness_s,
        "state": state,
    }
    if state is None or freshness_s is None or freshness_s > HEALTH_STALE_THRESHOLD:
        return result

    resource = state.get("resource_blocked") or {}
    if bool(resource.get("blocked")):
        return {
            **result,
            "status": "RESOURCE_BLOCKED",
            "exit_code": EXIT_RESOURCE_BLOCKED,
            "reason": resource.get("reason") or "resource_blocked",
        }

    gateway = state.get("gateway") or {}
    ready_age_s = _number(gateway.get("ready_age_s"), default=0.0)
    latency_ms = gateway.get("latency_ms")
    gateway_down = (
        not bool(gateway.get("connected"))
        or bool(gateway.get("closed"))
        or (
            isinstance(latency_ms, (int, float))
            and latency_ms >= HEALTH_GATEWAY_LATENCY_THRESHOLD_MS
        )
        or (
            not bool(gateway.get("ready"))
            and ready_age_s > HEALTH_READY_GRACE
        )
    )
    if gateway_down:
        return {
            **result,
            "status": "GATEWAY_DOWN",
            "exit_code": EXIT_GATEWAY_DOWN,
            "reason": "gateway_down",
        }

    event_loop = state.get("event_loop") or {}
    if _number(event_loop.get("lag_ms"), default=0.0) >= HEALTH_LOOP_LAG_THRESHOLD_MS:
        return {
            **result,
            "status": "EVENT_LOOP_LAG",
            "exit_code": EXIT_EVENT_LOOP_LAG,
            "reason": "event_loop_lag",
        }

    spotify = state.get("spotify") or {}
    spotify_enabled = bool(spotify.get("enabled"))
    if spotify_enabled and spotify.get("session_alive") is False:
        return {
            **result,
            "status": "SPOTIFY_DOWN",
            "exit_code": EXIT_SPOTIFY_DOWN,
            "reason": "spotify_down",
        }

    readiness = state.get("readiness") or {}
    if (
        readiness.get("slash_ready") is not True
        and ready_age_s > HEALTH_READY_GRACE
    ):
        return {
            **result,
            "status": "SLASH_NOT_READY",
            "exit_code": EXIT_SLASH_NOT_READY,
            "reason": "slash_not_ready",
        }

    audio_ready = readiness.get("audio_ready")
    if audio_ready is not True and ready_age_s > HEALTH_READY_GRACE and spotify_enabled:
        return {
            **result,
            "status": "AUDIO_NOT_READY",
            "exit_code": EXIT_AUDIO_NOT_READY,
            "reason": "audio_not_ready",
        }

    slash_acceptable = readiness.get("slash_ready") is True or (
        ready_age_s <= HEALTH_READY_GRACE
    )
    audio_acceptable = (
        audio_ready is True
        or (not spotify_enabled and audio_ready is None)
        or ready_age_s <= HEALTH_READY_GRACE
    )
    if slash_acceptable and audio_acceptable:
        return {
            **result,
            "status": "OK",
            "exit_code": EXIT_OK,
            "reason": "ok",
        }

    # A malformed readiness combination must never be reported as healthy.
    return {
        **result,
        "status": "AUDIO_NOT_READY",
        "exit_code": EXIT_AUDIO_NOT_READY,
        "reason": "audio_not_ready",
    }


def _number(value: Any, *, default: float) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def active_incident() -> dict[str, Any] | None:
    incident = read_json(HEALTH_INCIDENT_FILE)
    if incident is None or incident.get("recovered") is True:
        return None
    return incident


def _open_incident_locked(
    reason: str, exit_code: int, fault_boot_id: str | None = None
) -> tuple[dict[str, Any], bool]:
    incident = active_incident()
    if incident is not None:
        return incident, False

    from uuid import uuid4

    incident = {
        "incident_id": str(uuid4()),
        "reason": reason,
        "exit_code": exit_code,
        "fault_started_at_wall": utc_now(),
        "fault_started_at_monotonic": time.monotonic(),
        "fault_boot_id": fault_boot_id,
        "restart_triggered": False,
        "restart_status": "pending",
        "restart_triggered_at_wall": None,
        "ended_at_wall": None,
        "ended_at_monotonic": None,
        "recovered": False,
    }
    atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
    return incident, True


def open_incident(
    reason: str, exit_code: int, fault_boot_id: str | None = None
) -> tuple[dict[str, Any], bool]:
    with incident_state_lock():
        return _open_incident_locked(reason, exit_code, fault_boot_id)


def send_webhook(
    event: str, incident: dict[str, Any], *, event_id: str | None = None
) -> bool:
    if not ADMIN_ALERT_WEBHOOK:
        return False
    body = {
        "content": (
            f"Ugoku {event}: incident={incident['incident_id']} "
            f"reason={incident['reason']} exit={incident['exit_code']}"
        ),
        "event": event,
        "incident": incident,
    }
    if event_id is not None:
        body["event_id"] = event_id
    payload = json.dumps(body).encode("utf-8")
    request = urllib_request.Request(
        ADMIN_ALERT_WEBHOOK,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(request, timeout=HEALTH_ALERT_TIMEOUT) as response:
            response.read(1)
        return True
    except (OSError, TimeoutError, urllib_error.URLError):
        return False


def _trigger_restart_locked(incident: dict[str, Any]) -> bool:
    if incident.get("restart_triggered") or incident.get("restart_status") in {
        "submitting",
        "unknown",
        "accepted",
    }:
        return False
    incident["restart_status"] = "submitting"
    atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
    try:
        completed = subprocess.run(
            RESTART_COMMAND,
            check=False,
            shell=False,
            timeout=HEALTH_SLA_RESTART_TRIGGER_S,
        )
    except subprocess.TimeoutExpired:
        # systemctl may have accepted the job before the client timed out. Keep
        # the durable guard closed until recovery/manual diagnosis resolves it.
        incident["restart_status"] = "unknown"
        atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
        return False
    except (OSError, subprocess.SubprocessError):
        incident["restart_status"] = "failed"
        atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
        return False
    if completed.returncode != 0:
        incident["restart_status"] = "failed"
        atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
        return False

    incident["restart_triggered"] = True
    incident["restart_status"] = "accepted"
    incident["restart_triggered_at_wall"] = utc_now()
    atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
    _queue_alert_locked("RESTART", incident)
    return True


def trigger_restart(incident: dict[str, Any]) -> bool:
    with incident_state_lock():
        current = active_incident()
        if current is None or current.get("incident_id") != incident.get("incident_id"):
            return False
        restarted = _trigger_restart_locked(current)
        _ensure_incident_alerts_locked(current)
        _flush_outbox_locked()
        return restarted


def _strict_recovery_ready(diagnosis: dict[str, Any]) -> bool:
    if diagnosis.get("exit_code") != EXIT_OK:
        return False
    state = diagnosis.get("state") or {}
    gateway = state.get("gateway") or {}
    event_loop = state.get("event_loop") or {}
    readiness = state.get("readiness") or {}
    spotify = state.get("spotify") or {}
    resource = state.get("resource_blocked") or {}
    latency_ms = gateway.get("latency_ms")
    return bool(
        gateway.get("connected") is True
        and gateway.get("closed") is not True
        and gateway.get("ready") is True
        and not (
            isinstance(latency_ms, (int, float))
            and latency_ms >= HEALTH_GATEWAY_LATENCY_THRESHOLD_MS
        )
        and _number(event_loop.get("lag_ms"), default=0.0)
        < HEALTH_LOOP_LAG_THRESHOLD_MS
        and resource.get("blocked") is not True
        and readiness.get("slash_ready") is True
        and (
            readiness.get("audio_ready") is True
            or (
                not bool(spotify.get("enabled"))
                and readiness.get("audio_ready") is None
            )
        )
        and (
            not bool(spotify.get("enabled"))
            or spotify.get("session_alive") is True
        )
    )


def _healthy_new_boot(incident: dict[str, Any], diagnosis: dict[str, Any]) -> bool:
    if not _strict_recovery_ready(diagnosis):
        return False
    state = diagnosis.get("state") or {}
    current_boot_id = state.get("boot_id")
    fault_boot_id = incident.get("fault_boot_id")
    if not isinstance(current_boot_id, str) or not current_boot_id:
        return False
    if isinstance(fault_boot_id, str) and fault_boot_id:
        return current_boot_id != fault_boot_id
    try:
        incident_started = datetime.fromisoformat(
            str(incident["fault_started_at_wall"])
        ).timestamp()
    except (KeyError, TypeError, ValueError):
        return False
    snapshot_timestamp = state.get("timestamp")
    return bool(
        isinstance(snapshot_timestamp, (int, float))
        and float(snapshot_timestamp) > incident_started
    )


def _recover_incident_locked(diagnosis: dict[str, Any]) -> bool:
    incident = active_incident()
    if incident is None:
        _flush_outbox_locked()
        return False
    if not _healthy_new_boot(incident, diagnosis):
        return False
    if not incident.get("restart_triggered"):
        # A new healthy boot resolves a submitting/unknown client-side status:
        # systemd did perform a restart, so persist and alert that fact without
        # ever issuing another restart command.
        incident["restart_triggered"] = True
        incident["restart_status"] = "accepted"
        incident["restart_triggered_at_wall"] = (
            incident.get("restart_triggered_at_wall") or utc_now()
        )
        atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
    _ensure_incident_alerts_locked(incident)
    incident["ended_at_wall"] = utc_now()
    incident["ended_at_monotonic"] = time.monotonic()
    incident["recovered"] = True
    # Queue the final incident snapshot before closing the active incident so
    # a crash cannot lose RECOVERY while the queued event reports completion.
    _queue_alert_locked("RECOVERY", incident)
    atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
    write_failure_count(0)
    # Alert delivery is an independent durable concern. Operational recovery
    # closes now; any pending outbox entry remains ordered and retryable.
    _flush_outbox_locked()
    return True


def recover_incident(state_path: Path = HEALTH_STATE_FILE) -> bool:
    diagnosis = evaluate_state(state_path)
    with incident_state_lock():
        return _recover_incident_locked(diagnosis)


def run_probe(args: argparse.Namespace) -> int:
    diagnosis = evaluate_state(args.state)
    diagnosis["failure_threshold"] = args.threshold

    if args.json:
        diagnosis["failure_count"] = read_failure_count()
        print(json.dumps(diagnosis, sort_keys=True))
        return int(diagnosis["exit_code"])

    exit_code = int(diagnosis["exit_code"])
    with incident_state_lock():
        current_count = read_failure_count()
        diagnosis["failure_count"] = current_count
        if exit_code == EXIT_OK:
            write_failure_count(0)
            _recover_incident_locked(diagnosis)
        else:
            current_count += 1
            write_failure_count(current_count)
            diagnosis["failure_count"] = current_count
            if current_count >= args.threshold:
                state = diagnosis.get("state") or {}
                incident, _ = _open_incident_locked(
                    str(diagnosis["reason"]),
                    exit_code,
                    state.get("boot_id"),
                )
                _queue_alert_locked("OUTAGE", incident)
                if not args.no_restart:
                    _trigger_restart_locked(incident)
                _ensure_incident_alerts_locked(incident)
                _flush_outbox_locked()

    print(json.dumps(diagnosis, sort_keys=True))
    return exit_code


def run_on_failure() -> int:
    state = read_json(HEALTH_STATE_FILE) or {}
    with incident_state_lock():
        incident, _ = _open_incident_locked(
            "watchdog", EXIT_EVENT_LOOP_LAG, state.get("boot_id")
        )
        if not incident.get("restart_triggered"):
            incident["restart_triggered"] = True
            incident["restart_status"] = "accepted"
            incident["restart_triggered_at_wall"] = utc_now()
            atomic_write_json(HEALTH_INCIDENT_FILE, incident, INCIDENT_MODE)
        _ensure_incident_alerts_locked(incident)
        _flush_outbox_locked()
    print(json.dumps({"status": "OUTAGE", "incident": incident}, sort_keys=True))
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--on-failure", action="store_true")
    modes.add_argument("--recover", action="store_true")
    parser.add_argument("--state", type=Path, default=HEALTH_STATE_FILE)
    parser.add_argument("--threshold", type=int, default=HEALTH_FAILURE_THRESHOLD)
    parser.add_argument("--no-restart", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.threshold < 1:
        raise SystemExit("--threshold must be at least 1")
    if args.on_failure:
        return run_on_failure()
    if args.recover:
        recovered = recover_incident(args.state)
        print(json.dumps({"status": "RECOVERED" if recovered else "NOT_RECOVERED"}))
        return EXIT_OK
    return run_probe(args)


if __name__ == "__main__":
    raise SystemExit(main())
