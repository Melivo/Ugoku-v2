import argparse
import inspect
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")

from scripts import healthcheck


def healthy_state():
    return {
        "boot_id": "boot-new",
        "timestamp": time.time(),
        "gateway": {
            "connected": True,
            "closed": False,
            "ready": True,
            "ready_age_s": healthcheck.HEALTH_READY_GRACE + 1,
            "latency_ms": 10,
        },
        "event_loop": {"lag_ms": 0},
        "spotify": {"enabled": True, "session_alive": True},
        "readiness": {"slash_ready": True, "audio_ready": True},
        "resource_blocked": {"blocked": False, "reason": None},
    }


def write_state(path, state):
    path.write_text(json.dumps(state), encoding="utf-8")


class HealthcheckExitStateTests(unittest.TestCase):
    def test_all_health_exit_states_and_evaluation_order(self):
        with tempfile.TemporaryDirectory() as directory:
            state_path = Path(directory) / "health.json"
            cases = []

            state = healthy_state()
            cases.append(("ok", state, healthcheck.EXIT_OK))
            state = healthy_state()
            state["resource_blocked"] = {"blocked": True, "reason": "voice"}
            cases.append(("resource", state, healthcheck.EXIT_RESOURCE_BLOCKED))
            state = healthy_state()
            state["gateway"]["connected"] = False
            cases.append(("gateway", state, healthcheck.EXIT_GATEWAY_DOWN))
            state = healthy_state()
            state["event_loop"]["lag_ms"] = healthcheck.HEALTH_LOOP_LAG_THRESHOLD_MS
            cases.append(("lag", state, healthcheck.EXIT_EVENT_LOOP_LAG))
            state = healthy_state()
            state["spotify"]["session_alive"] = False
            cases.append(("spotify", state, healthcheck.EXIT_SPOTIFY_DOWN))
            state = healthy_state()
            state["readiness"]["slash_ready"] = False
            cases.append(("slash", state, healthcheck.EXIT_SLASH_NOT_READY))
            state = healthy_state()
            state["readiness"]["audio_ready"] = False
            cases.append(("audio", state, healthcheck.EXIT_AUDIO_NOT_READY))

            for name, state, expected in cases:
                with self.subTest(name=name):
                    write_state(state_path, state)
                    self.assertEqual(
                        healthcheck.evaluate_state(state_path)["exit_code"], expected
                    )

            self.assertEqual(
                healthcheck.evaluate_state(Path(directory) / "missing.json")["exit_code"],
                healthcheck.EXIT_STALE,
            )
            write_state(state_path, healthy_state())
            old = time.time() - healthcheck.HEALTH_STALE_THRESHOLD - 1
            os.utime(state_path, (old, old))
            self.assertEqual(
                healthcheck.evaluate_state(state_path)["exit_code"],
                healthcheck.EXIT_STALE,
            )

            priority = healthy_state()
            priority["resource_blocked"] = {"blocked": True, "reason": "ffmpeg"}
            priority["gateway"]["connected"] = False
            priority["event_loop"]["lag_ms"] = 999999
            write_state(state_path, priority)
            self.assertEqual(
                healthcheck.evaluate_state(state_path)["exit_code"],
                healthcheck.EXIT_RESOURCE_BLOCKED,
            )

    def test_gateway_down_or_predicates_and_ready_grace(self):
        variants = (
            ("not_connected", lambda state: state["gateway"].update(connected=False)),
            ("closed", lambda state: state["gateway"].update(closed=True)),
            (
                "latency",
                lambda state: state["gateway"].update(
                    latency_ms=healthcheck.HEALTH_GATEWAY_LATENCY_THRESHOLD_MS
                ),
            ),
            ("not_ready", lambda state: state["gateway"].update(ready=False)),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "health.json"
            for name, mutate in variants:
                with self.subTest(name=name):
                    state = healthy_state()
                    mutate(state)
                    write_state(path, state)
                    self.assertEqual(
                        healthcheck.evaluate_state(path)["exit_code"],
                        healthcheck.EXIT_GATEWAY_DOWN,
                    )

            state = healthy_state()
            state["gateway"].update(ready=False, ready_age_s=0)
            state["readiness"].update(slash_ready=False, audio_ready=False)
            write_state(path, state)
            self.assertEqual(
                healthcheck.evaluate_state(path)["exit_code"], healthcheck.EXIT_OK
            )

    def test_audio_na_is_only_healthy_when_spotify_is_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "health.json"
            state = healthy_state()
            state["readiness"]["audio_ready"] = None
            write_state(path, state)
            self.assertEqual(
                healthcheck.evaluate_state(path)["exit_code"],
                healthcheck.EXIT_AUDIO_NOT_READY,
            )

            state["spotify"]["enabled"] = False
            write_state(path, state)
            self.assertEqual(healthcheck.evaluate_state(path)["exit_code"], 0)

            state["readiness"]["audio_ready"] = False
            write_state(path, state)
            self.assertEqual(
                healthcheck.evaluate_state(path)["exit_code"],
                healthcheck.EXIT_AUDIO_NOT_READY,
            )


class HealthcheckIncidentLifecycleTests(unittest.TestCase):
    def test_all_incident_transition_entry_points_take_the_process_lock(self):
        lock_source = inspect.getsource(healthcheck.incident_state_lock)
        self.assertIn("fcntl.flock", lock_source)
        self.assertIn("fcntl.LOCK_EX", lock_source)
        for function in (
            healthcheck.open_incident,
            healthcheck.trigger_restart,
            healthcheck.recover_incident,
            healthcheck.run_probe,
            healthcheck.run_on_failure,
        ):
            with self.subTest(function=function.__name__):
                self.assertIn(
                    "with incident_state_lock()", inspect.getsource(function)
                )

    def test_incident_webhook_message_contains_event_reason_exit_and_id(self):
        incident = {
            "incident_id": "incident-123",
            "reason": "gateway_down",
            "exit_code": healthcheck.EXIT_GATEWAY_DOWN,
        }
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read = Mock(return_value=b"")
        with patch.object(
            healthcheck, "ADMIN_ALERT_WEBHOOK", "https://discord.example/webhook"
        ), patch.object(
            healthcheck.urllib_request, "urlopen", return_value=response
        ) as urlopen:
            self.assertTrue(healthcheck.send_webhook("OUTAGE", incident))

        request = urlopen.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["event"], "OUTAGE")
        self.assertEqual(payload["incident"], incident)
        self.assertEqual(
            payload["content"],
            "Ugoku OUTAGE: incident=incident-123 reason=gateway_down exit=3",
        )
        self.assertEqual(request.get_header("User-agent"), "Ugoku-Monitor/1.0")
        self.assertEqual(
            urlopen.call_args.kwargs["timeout"], healthcheck.HEALTH_ALERT_TIMEOUT
        )

    def test_two_strikes_one_restart_and_shared_incident_messages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            fail_path = root / "fail.count"
            incident_path = root / "incident.json"
            state = healthy_state()
            state["gateway"]["connected"] = False
            write_state(state_path, state)
            args = argparse.Namespace(
                state=state_path, threshold=2, json=False, no_restart=False
            )
            events = []

            def record(event, incident, **_kwargs):
                events.append((event, incident["incident_id"]))
                return True

            with patch.multiple(
                healthcheck,
                HEALTH_FAIL_COUNT_FILE=fail_path,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(healthcheck, "send_webhook", side_effect=record), patch.object(
                healthcheck.subprocess, "run", return_value=Mock(returncode=0)
            ) as restart:
                self.assertEqual(healthcheck.run_probe(args), 3)
                self.assertEqual(events, [])
                self.assertEqual(healthcheck.run_probe(args), 3)
                self.assertEqual(healthcheck.run_probe(args), 3)
                recovered_state = healthy_state()
                recovered_state["boot_id"] = "boot-recovered"
                write_state(state_path, recovered_state)
                self.assertTrue(healthcheck.recover_incident(state_path))
                self.assertFalse(healthcheck.recover_incident(state_path))

            self.assertEqual([event for event, _ in events], ["OUTAGE", "RESTART", "RECOVERY"])
            self.assertEqual(len({incident_id for _, incident_id in events}), 1)
            restart.assert_called_once_with(
                healthcheck.RESTART_COMMAND,
                check=False,
                shell=False,
                timeout=healthcheck.HEALTH_SLA_RESTART_TRIGGER_S,
            )
            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            self.assertTrue(incident["restart_triggered"])
            self.assertTrue(incident["recovered"])
            self.assertEqual(fail_path.read_text(encoding="utf-8").strip(), "0")

    def test_on_failure_and_recover_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incident_path = root / "incident.json"
            fail_path = root / "fail.count"
            state_path = root / "health.json"
            failed_state = healthy_state()
            failed_state["boot_id"] = "watchdog-boot"
            write_state(state_path, failed_state)
            events = []
            with patch.multiple(
                healthcheck,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_FAIL_COUNT_FILE=fail_path,
                HEALTH_STATE_FILE=state_path,
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(
                healthcheck,
                "send_webhook",
                side_effect=lambda event, incident, **_kwargs: (
                    events.append((event, incident["incident_id"])) or True
                ),
            ), patch.object(healthcheck.subprocess, "run") as restart:
                self.assertEqual(healthcheck.run_on_failure(), 0)
                self.assertEqual(healthcheck.run_on_failure(), 0)
                recovered_state = healthy_state()
                recovered_state["boot_id"] = "replacement-boot"
                write_state(state_path, recovered_state)
                self.assertEqual(
                    healthcheck.main(["--recover", "--state", str(state_path)]), 0
                )
                self.assertEqual(
                    healthcheck.main(["--recover", "--state", str(state_path)]), 0
                )

            self.assertEqual(
                [event for event, _ in events], ["OUTAGE", "RESTART", "RECOVERY"]
            )
            self.assertEqual(len({incident_id for _, incident_id in events}), 1)
            restart.assert_not_called()

    def test_nonzero_restart_is_not_persisted_or_alerted_and_remains_retryable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            fail_path = root / "fail.count"
            incident_path = root / "incident.json"
            state = healthy_state()
            state["boot_id"] = "failed-boot"
            state["gateway"]["connected"] = False
            write_state(state_path, state)
            args = argparse.Namespace(
                state=state_path, threshold=1, json=False, no_restart=False
            )
            events = []
            with patch.multiple(
                healthcheck,
                HEALTH_FAIL_COUNT_FILE=fail_path,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(
                healthcheck,
                "send_webhook",
                side_effect=lambda event, incident, **_kwargs: (
                    events.append(event) or True
                ),
            ), patch.object(
                healthcheck.subprocess,
                "run",
                return_value=Mock(returncode=1),
            ) as restart:
                self.assertEqual(healthcheck.run_probe(args), healthcheck.EXIT_GATEWAY_DOWN)
                self.assertEqual(healthcheck.run_probe(args), healthcheck.EXIT_GATEWAY_DOWN)

            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            self.assertFalse(incident["restart_triggered"])
            self.assertIsNone(incident["restart_triggered_at_wall"])
            self.assertEqual(events, ["OUTAGE"])
            self.assertEqual(restart.call_count, 2)

    def test_recovery_requires_exit_ok_and_a_different_boot_id(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            incident_path = root / "incident.json"
            fail_path = root / "fail.count"
            with patch.multiple(
                healthcheck,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_FAIL_COUNT_FILE=fail_path,
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(healthcheck, "send_webhook", return_value=True) as webhook:
                healthcheck.open_incident(
                    "gateway_down", healthcheck.EXIT_GATEWAY_DOWN, "fault-boot"
                )

                unhealthy = healthy_state()
                unhealthy["boot_id"] = "replacement-boot"
                unhealthy["gateway"]["connected"] = False
                write_state(state_path, unhealthy)
                self.assertFalse(healthcheck.recover_incident(state_path))

                same_boot = healthy_state()
                same_boot["boot_id"] = "fault-boot"
                write_state(state_path, same_boot)
                self.assertFalse(healthcheck.recover_incident(state_path))

                replacement = healthy_state()
                replacement["boot_id"] = "replacement-boot"
                write_state(state_path, replacement)
                self.assertTrue(healthcheck.recover_incident(state_path))

            self.assertEqual(
                [call.args[0] for call in webhook.call_args_list],
                ["OUTAGE", "RESTART", "RECOVERY"],
            )

    def test_recovery_without_fault_boot_id_requires_post_incident_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            incident_path = root / "incident.json"
            outbox_path = root / "alert-outbox.json"
            with patch.multiple(
                healthcheck,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_FAIL_COUNT_FILE=root / "fail.count",
                HEALTH_ALERT_OUTBOX_FILE=outbox_path,
            ), patch.object(healthcheck, "send_webhook", return_value=True):
                incident, _ = healthcheck.open_incident(
                    "watchdog", healthcheck.EXIT_EVENT_LOOP_LAG, None
                )
                started = healthcheck.datetime.fromisoformat(
                    incident["fault_started_at_wall"]
                ).timestamp()

                old_snapshot = healthy_state()
                old_snapshot["timestamp"] = started - 1
                write_state(state_path, old_snapshot)
                self.assertFalse(healthcheck.recover_incident(state_path))

                new_snapshot = healthy_state()
                new_snapshot["timestamp"] = started + 1
                write_state(state_path, new_snapshot)
                self.assertTrue(healthcheck.recover_incident(state_path))

    def test_recovery_is_strict_but_does_not_wait_for_alert_delivery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            incident_path = root / "incident.json"
            outbox_path = root / "alert-outbox.json"
            with patch.multiple(
                healthcheck,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_FAIL_COUNT_FILE=root / "fail.count",
                HEALTH_ALERT_OUTBOX_FILE=outbox_path,
            ):
                healthcheck.open_incident(
                    "gateway_down", healthcheck.EXIT_GATEWAY_DOWN, "old-boot"
                )
                grace_false_positive = healthy_state()
                grace_false_positive["boot_id"] = "new-boot"
                grace_false_positive["gateway"]["ready_age_s"] = 0
                grace_false_positive["readiness"]["slash_ready"] = False
                write_state(state_path, grace_false_positive)
                with patch.object(healthcheck, "send_webhook") as webhook:
                    self.assertFalse(healthcheck.recover_incident(state_path))
                    webhook.assert_not_called()

                write_state(state_path, healthy_state())
                delivery_results = iter([False, True, True, True])
                with patch.object(
                    healthcheck,
                    "send_webhook",
                    side_effect=lambda *_args, **_kwargs: next(delivery_results),
                ):
                    self.assertTrue(healthcheck.recover_incident(state_path))
                    self.assertTrue(
                        json.loads(incident_path.read_text(encoding="utf-8"))[
                            "recovered"
                        ]
                    )
                    self.assertFalse(healthcheck.recover_incident(state_path))

            outbox = json.loads(outbox_path.read_text(encoding="utf-8"))
            self.assertEqual(
                [event["kind"] for event in outbox["events"]],
                ["OUTAGE", "RESTART", "RECOVERY"],
            )
            self.assertTrue(all(event["delivered"] for event in outbox["events"]))
            self.assertEqual(outbox["events"][0]["attempts"], 2)

    def test_pending_recovery_does_not_block_next_incident_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            incident_path = root / "incident.json"
            outbox_path = root / "alert-outbox.json"
            fail_path = root / "fail.count"
            args = argparse.Namespace(
                state=state_path, threshold=1, json=False, no_restart=False
            )
            with patch.multiple(
                healthcheck,
                HEALTH_INCIDENT_FILE=incident_path,
                HEALTH_FAIL_COUNT_FILE=fail_path,
                HEALTH_ALERT_OUTBOX_FILE=outbox_path,
            ), patch.object(
                healthcheck, "send_webhook", return_value=False
            ), patch.object(
                healthcheck.subprocess, "run", return_value=Mock(returncode=0)
            ) as restart:
                healthcheck.open_incident(
                    "gateway_down", healthcheck.EXIT_GATEWAY_DOWN, "old-boot"
                )
                replacement = healthy_state()
                replacement["boot_id"] = "new-boot"
                write_state(state_path, replacement)
                self.assertTrue(healthcheck.recover_incident(state_path))

                unhealthy = healthy_state()
                unhealthy["boot_id"] = "new-boot"
                unhealthy["gateway"]["connected"] = False
                write_state(state_path, unhealthy)
                self.assertEqual(
                    healthcheck.run_probe(args), healthcheck.EXIT_GATEWAY_DOWN
                )

            restart.assert_called_once()
            incident = json.loads(incident_path.read_text(encoding="utf-8"))
            self.assertTrue(incident["restart_triggered"])
            outbox = json.loads(outbox_path.read_text(encoding="utf-8"))
            prior_recovery = next(
                event for event in outbox["events"] if event["kind"] == "RECOVERY"
            )
            self.assertFalse(prior_recovery["delivered"])

    def test_restart_timeout_is_deduplicated_while_status_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            state = healthy_state()
            state["gateway"]["connected"] = False
            write_state(state_path, state)
            args = argparse.Namespace(
                state=state_path, threshold=1, json=False, no_restart=False
            )
            with patch.multiple(
                healthcheck,
                HEALTH_FAIL_COUNT_FILE=root / "fail.count",
                HEALTH_INCIDENT_FILE=root / "incident.json",
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(
                healthcheck, "send_webhook", return_value=True
            ), patch.object(
                healthcheck.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired(
                    healthcheck.RESTART_COMMAND,
                    healthcheck.HEALTH_SLA_RESTART_TRIGGER_S,
                ),
            ) as restart:
                healthcheck.run_probe(args)
                healthcheck.run_probe(args)

            self.assertEqual(restart.call_count, 1)
            incident = json.loads(
                (root / "incident.json").read_text(encoding="utf-8")
            )
            self.assertEqual(incident["restart_status"], "unknown")
            self.assertFalse(incident["restart_triggered"])

    def test_json_mode_has_no_counter_incident_restart_or_webhook_side_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_path = root / "health.json"
            write_state(state_path, healthy_state())
            args = argparse.Namespace(
                state=state_path, threshold=2, json=True, no_restart=False
            )
            with patch.multiple(
                healthcheck,
                HEALTH_FAIL_COUNT_FILE=root / "fail.count",
                HEALTH_INCIDENT_FILE=root / "incident.json",
                HEALTH_ALERT_OUTBOX_FILE=root / "alert-outbox.json",
            ), patch.object(healthcheck, "write_failure_count") as write_count, patch.object(
                healthcheck, "send_webhook"
            ) as webhook, patch.object(healthcheck.subprocess, "run") as restart:
                self.assertEqual(healthcheck.run_probe(args), 0)
            write_count.assert_not_called()
            webhook.assert_not_called()
            restart.assert_not_called()

    def test_oneshot_without_notify_socket_or_running_bot(self):
        script = Path(healthcheck.__file__).resolve()
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-health.json"
            env = os.environ.copy()
            env.pop("NOTIFY_SOCKET", None)
            env["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
            completed = subprocess.run(
                [sys.executable, str(script), "--state", str(missing), "--json"],
                cwd=script.parents[1],
                env=env,
                text=True,
                capture_output=True,
                check=False,
                timeout=10,
            )
        self.assertEqual(completed.returncode, healthcheck.EXIT_STALE)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["status"], "STALE")
