import asyncio
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from bot.health.audio_probe import AudioProbeResult
from bot.health.monitor import HealthMonitor
from bot.vocal.session_manager import session_manager


def healthy_bot():
    command = SimpleNamespace(name="health")
    return SimpleNamespace(
        is_ready=lambda: True,
        is_closed=lambda: False,
        latency=0.025,
        ws=SimpleNamespace(open=True, closed=False),
        application_commands=[command],
    )


class HealthMonitorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_sessions = dict(session_manager.server_sessions)
        session_manager.server_sessions.clear()

    def tearDown(self):
        session_manager.server_sessions.clear()
        session_manager.server_sessions.update(self.original_sessions)

    async def test_start_notifies_ready_once_and_uses_one_task(self):
        monitor = HealthMonitor(healthy_bot())
        release = asyncio.Event()

        async def parked_loop():
            await release.wait()

        monitor._run = parked_loop
        monitor._sd_notify = Mock()
        monitor.run_readiness_probe = AsyncMock()
        monitor.write_state = AsyncMock(
            return_value={
                "version": 1,
                "boot_id": monitor.boot_id,
                "timestamp": 1.0,
                "gateway": {},
                "readiness": {"last_check_monotonic": 1.0},
            }
        )

        await monitor.start()
        first_task = monitor._task
        await monitor.start()

        self.assertIs(monitor._task, first_task)
        monitor._sd_notify.assert_called_once_with("READY=1")
        await monitor.stop()
        self.assertIsNone(monitor._task)

    async def test_start_does_not_send_ready_for_invalid_initial_snapshot(self):
        monitor = HealthMonitor(healthy_bot())
        monitor._sd_notify = Mock()
        monitor.run_readiness_probe = AsyncMock()
        monitor.write_state = AsyncMock(return_value={"version": 1})

        with self.assertRaises(RuntimeError):
            await monitor.start()

        monitor._sd_notify.assert_not_called()
        self.assertFalse(monitor._ready_notified)
        self.assertIsNone(monitor._task)

    def test_sd_notify_without_notify_socket_is_a_noop(self):
        monitor = HealthMonitor(healthy_bot())
        with patch.dict(os.environ, {}, clear=True), patch(
            "bot.health.monitor.socket.socket"
        ) as socket_factory:
            monitor._sd_notify("WATCHDOG=1")
        socket_factory.assert_not_called()

    async def test_write_state_is_atomic_complete_and_observable_only(self):
        monitor = HealthMonitor(healthy_bot())
        monitor._readiness = {
            "slash_ready": True,
            "audio_ready": None,
            "last_check_monotonic": 1.0,
        }
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "health.json"
            incident_path = Path(directory) / "incident.json"
            count_path = Path(directory) / "fail.count"
            with patch("bot.health.monitor.HEALTH_STATE_FILE", state_path), patch(
                "bot.health.monitor.os.chmod", wraps=os.chmod
            ) as chmod:
                await monitor.write_state()

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["version"], 1)
            self.assertTrue(state["gateway"]["connected"])
            self.assertTrue(state["readiness"]["slash_ready"])
            self.assertNotIn("incident_id", state)
            chmod.assert_called_once_with(chmod.call_args.args[0], 0o644)
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(state_path.stat().st_mode), 0o644)
            self.assertFalse(incident_path.exists())
            self.assertFalse(count_path.exists())
            self.assertEqual(list(state_path.parent.glob("*.tmp")), [])

    async def test_readiness_probe_is_single_flight_cooled_down_and_queue_isolated(self):
        monitor = HealthMonitor(healthy_bot())
        before = dict(session_manager.server_sessions)
        result = AudioProbeResult(True, "spotify", 0.01, 8192, None)

        with patch(
            "bot.health.monitor.probe_audio", new=AsyncMock(return_value=result)
        ) as probe:
            first, second = await asyncio.gather(
                monitor.run_readiness_probe(), monitor.run_readiness_probe()
            )
            third = await monitor.run_readiness_probe()

        self.assertEqual(probe.await_count, 1)
        self.assertTrue(first["slash_ready"])
        self.assertTrue(second["audio_ready"])
        self.assertEqual(third["audio_probe"]["bytes_read"], 8192)
        self.assertEqual(session_manager.server_sessions, before)

    def test_slash_readiness_requires_registered_health_command(self):
        bot = healthy_bot()
        monitor = HealthMonitor(bot)
        self.assertTrue(monitor._slash_command_ready())

        bot.application_commands = [SimpleNamespace(name="other")]
        self.assertFalse(monitor._slash_command_ready())

        bot.application_commands = None
        bot.pending_application_commands = {"x": SimpleNamespace(name="health")}
        self.assertTrue(monitor._slash_command_ready())
