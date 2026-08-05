import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HealthPathConfigTests(unittest.TestCase):
    def test_empty_path_environment_values_use_run_defaults(self):
        env = os.environ.copy()
        env["UGOKU_RUN_DIR"] = ""
        env["UGOKU_HEALTH_STATE_FILE"] = ""
        env.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json, config; "
                    "print(json.dumps([config.HEALTH_RUN_DIR.as_posix(), "
                    "config.HEALTH_STATE_FILE.as_posix()]))"
                ),
            ],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=True,
            timeout=10,
        )

        self.assertEqual(
            json.loads(completed.stdout),
            ["/run/ugoku", "/run/ugoku/health.json"],
        )
