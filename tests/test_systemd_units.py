import json
import unittest
from pathlib import Path

import config
from scripts import healthcheck


ROOT = Path(__file__).resolve().parents[1]


class SystemdUnitStaticTests(unittest.TestCase):
    def test_bot_service_is_hardened_and_has_strict_ready_recovery_hook(self):
        content = (ROOT / "deploy" / "ugoku.service").read_text(encoding="utf-8")
        for directive in (
            "NoNewPrivileges=true",
            "ProtectSystem=full",
            "PrivateTmp=true",
            "CapabilityBoundingSet=",
            "UMask=0077",
        ):
            self.assertIn(directive, content)
        self.assertIn("ExecStartPost=", content)
        self.assertIn("scripts/healthcheck.py --recover", content)
        self.assertIn("Type=notify", content)
        self.assertIn("ExecStart=/home/leadt3ch/.local/bin/uv run", content)
        self.assertIn("NotifyAccess=all", content)
        self.assertEqual(config.HEALTH_SLA_BOOT_READY_S, 30)
        unit_start_budget = (
            config.HEALTH_SLA_BOOT_READY_S
            + config.HEALTH_SLA_RECOVERY_ALERT_S
        )
        self.assertEqual(unit_start_budget, 35)
        self.assertIn(f"TimeoutStartSec={unit_start_budget}s", content)

    def test_unit_deploy_install_uses_legacy_cpu_numpy_constraint(self):
        service = (ROOT / "deploy" / "ugoku.service").read_text(encoding="utf-8")
        runbook = (
            ROOT / "docs" / "runbooks" / "bot-produktionsueberwachung.md"
        ).read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        constraint = (
            ROOT / "deploy" / "constraints-linux-legacy-cpu.txt"
        ).read_text(encoding="utf-8")

        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("numpy==2.1.3", constraint)
        self.assertIn("py-cord[voice]>=2.8.1,<3.0.0", requirements.splitlines())
        for documented_install_path in (service, runbook, readme):
            with self.subTest(path=documented_install_path[:40]):
                self.assertIn("-r requirements.txt", documented_install_path)
                self.assertIn(
                    "-c deploy/constraints-linux-legacy-cpu.txt",
                    documented_install_path,
                )
                self.assertIn(
                    "assert numpy.__version__ == '2.1.3'",
                    documented_install_path,
                )
        self.assertLess(
            runbook.index("-c deploy/constraints-linux-legacy-cpu.txt"),
            runbook.index("systemctl enable --now ugoku.service"),
        )

    def test_machine_readable_plan_uses_current_recovery_contract(self):
        plan_path = ROOT / ".agents" / "results" / "plan-20260805-000000.json"
        plan_text = plan_path.read_text(encoding="utf-8")
        plan = json.loads(plan_text)

        self.assertEqual(plan["phase"], "IMPLEMENTED")
        self.assertEqual(plan["status"], "ACTIVE")
        revision = plan["ccr_revision_4"]
        self.assertEqual(revision["status"], "implemented")
        self.assertIn("RECOVERY durable queued", revision["operational_recovery"])
        self.assertIn("independent", revision["delivery"])
        self.assertIn("NotifyAccess=all", revision["notify_access"])
        self.assertEqual(revision["unit_start_budget_s"], 35)
        self.assertIn("TimeoutStartSec=35s", revision["unit_activation"])
        self.assertNotIn("erst nach zugestelltem RECOVERY", plan_text)

    def test_external_units_keep_filesystem_tmp_and_capability_hardening(self):
        for name in ("ugoku-health.service", "ugoku-alert-onfailure.service"):
            content = (ROOT / "deploy" / name).read_text(encoding="utf-8")
            with self.subTest(unit=name):
                self.assertIn("ProtectSystem=full", content)
                self.assertIn("ReadWritePaths=/run/ugoku", content)
                self.assertIn("PrivateTmp=true", content)
                self.assertIn("CapabilityBoundingSet=", content)

        alert = (ROOT / "deploy" / "ugoku-alert-onfailure.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("NoNewPrivileges=true", alert)

    def test_restart_sudoers_matches_non_blocking_command_exactly(self):
        content = (ROOT / "deploy" / "ugoku-restart.sudoers").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            content.strip(),
            "leadt3ch ALL=(root) NOPASSWD: /bin/systemctl --no-block restart ugoku.service",
        )
        self.assertEqual(
            healthcheck.RESTART_COMMAND,
            [
                "sudo",
                "-n",
                "/bin/systemctl",
                "--no-block",
                "restart",
                "ugoku.service",
            ],
        )

    def test_onfailure_finishes_fault_context_capture_before_restart(self):
        bot = (ROOT / "deploy" / "ugoku.service").read_text(encoding="utf-8")
        alert = (ROOT / "deploy" / "ugoku-alert-onfailure.service").read_text(
            encoding="utf-8"
        )
        self.assertIn("OnFailure=ugoku-alert-onfailure.service", bot)
        self.assertIn("Before=ugoku.service", alert)
        self.assertNotIn("After=ugoku.service", alert)
        self.assertNotIn("Requires=ugoku.service", alert)

    def test_timer_restart_stop_and_recovery_fit_total_sla(self):
        timer = (ROOT / "deploy" / "ugoku-health.timer").read_text(
            encoding="utf-8"
        )
        service = (ROOT / "deploy" / "ugoku.service").read_text(encoding="utf-8")
        self.assertIn("OnUnitActiveSec=110s", timer)
        self.assertIn("AccuracySec=2s", timer)
        self.assertIn(f"RestartSec={config.HEALTH_SLA_RESTART_SEC_S}", service)
        self.assertIn(f"TimeoutStopSec={config.HEALTH_SLA_STOP_S}", service)
        self.assertEqual(config.HEALTH_SLA_BOOT_READY_S, 30)
        unit_start_budget = (
            config.HEALTH_SLA_BOOT_READY_S
            + config.HEALTH_SLA_RECOVERY_ALERT_S
        )
        self.assertEqual(unit_start_budget, 35)
        self.assertIn(f"TimeoutStartSec={unit_start_budget}s", service)

        timer_detection = config.HEALTH_FAILURE_THRESHOLD * (110 + 2)
        self.assertLessEqual(timer_detection, config.HEALTH_SLA_DETECT_S)
        total_budget = sum(
            (
                config.HEALTH_SLA_DETECT_S,
                config.HEALTH_SLA_RESTART_TRIGGER_S,
                config.HEALTH_SLA_STOP_S,
                config.HEALTH_SLA_RESTART_SEC_S,
                config.HEALTH_SLA_BOOT_READY_S,
                config.HEALTH_SLA_RECOVERY_ALERT_S,
            )
        )
        self.assertEqual(total_budget, 295)
        self.assertLessEqual(total_budget, config.HEALTH_SLA_TOTAL_S)
