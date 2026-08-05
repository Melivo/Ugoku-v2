#!/usr/bin/env python3
"""Unit tests for the Serena safety utility."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import serena_safety


class SerenaSafetyTests(unittest.TestCase):
    def test_writes_missing_playbook(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agents = Path(temp) / "AGENTS.md"
            result = serena_safety.update_agents(agents, apply=True)
            text = agents.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "written")
            self.assertEqual(text.count(serena_safety.START), 1)
            self.assertIn("Never run broad Serena", text)

    def test_preserves_equivalent_existing_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agents = Path(temp) / "AGENTS.md"
            original = "Never run broad Serena searches. Expand sequentially. After a timeout, use Serena CLI.\n"
            agents.write_text(original, encoding="utf-8")
            result = serena_safety.update_agents(agents, apply=True)
            self.assertEqual(result["status"], "equivalent-existing")
            self.assertEqual(agents.read_text(encoding="utf-8"), original)

    def test_replaces_managed_block_without_duplication(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            agents = Path(temp) / "AGENTS.md"
            agents.write_text(
                f"Header\n\n{serena_safety.START}\nold\n{serena_safety.END}\n",
                encoding="utf-8",
            )
            serena_safety.update_agents(agents, apply=True)
            text = agents.read_text(encoding="utf-8")
            self.assertEqual(text.count(serena_safety.START), 1)
            self.assertNotIn("\nold\n", text)

    def test_updates_existing_complete_global_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / ".serena" / "serena_config.yml"
            config.parent.mkdir()
            config.write_text("projects: []\ntool_timeout: 30.0\n", encoding="utf-8")
            result = serena_safety.set_global_timeout(config, apply=True)
            self.assertEqual(result["value"], 10.0)
            self.assertIn("tool_timeout: 10.0", config.read_text(encoding="utf-8"))

    def test_flags_project_tool_timeout_as_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "project.yml"
            project.write_text("project_name: demo\ntool_timeout: 10\n", encoding="utf-8")
            result = serena_safety.inspect_project_config(project)
            self.assertEqual(result["status"], "unsupported-key")

    def test_reads_yaml_list_tool_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "servers.yaml"
            config.write_text(
                "serena:\n  timeout: 10000\n  command:\n    - serena\n    - --tool-timeout\n    - \"10\"\n",
                encoding="utf-8",
            )
            result = serena_safety.inspect_client_config(config)
            self.assertTrue(result["tool_timeout_10"])
            self.assertTrue(result["client_timeout_10s"])

    def test_detects_only_project_source_languages(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
            (root / ".agents" / "skills").mkdir(parents=True)
            (root / ".agents" / "skills" / "helper.py").write_text("pass\n", encoding="utf-8")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "main.py").write_text("pass\n", encoding="utf-8")
            self.assertEqual(serena_safety.detect_project_languages(root), {"typescript": 1})

    def test_detects_multiple_real_source_languages_by_count(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "main.py").write_text("pass\n", encoding="utf-8")
            (root / "src" / "one.ts").write_text("export {};\n", encoding="utf-8")
            (root / "src" / "two.ts").write_text("export {};\n", encoding="utf-8")
            self.assertEqual(serena_safety.detect_project_languages(root), {"typescript": 2, "python": 1})

    def test_omits_low_signal_helper_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            for index in range(20):
                (root / "src" / f"module-{index}.ts").write_text("export {};\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "helper.py").write_text("pass\n", encoding="utf-8")
            self.assertEqual(serena_safety.detect_project_languages(root), {"typescript": 20})

    def test_replaces_extra_project_languages(self) -> None:
        text = "languages:\n- typescript\n- python\n\nencoding: utf-8\n"
        updated = serena_safety.replace_configured_languages(text, ["typescript"])
        self.assertEqual(serena_safety.parse_configured_languages(updated), ["typescript"])
        self.assertNotIn("- python", updated)
        self.assertIn("encoding: utf-8", updated)

    def test_updates_inline_project_languages_idempotently(self) -> None:
        text = "languages: [python, typescript]\nencoding: utf-8\n"
        updated = serena_safety.replace_configured_languages(text, ["typescript"])
        self.assertEqual(serena_safety.parse_configured_languages(updated), ["typescript"])
        self.assertEqual(serena_safety.replace_configured_languages(updated, ["typescript"]), updated)

    def test_writes_valid_empty_language_list(self) -> None:
        text = "languages:\n- python\nencoding: utf-8\n"
        updated = serena_safety.replace_configured_languages(text, [])
        self.assertEqual(serena_safety.parse_configured_languages(updated), [])
        self.assertIn("languages: []", updated)

    def test_updates_effective_project_local_language_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "src").mkdir()
            (root / "src" / "index.ts").write_text("export {};\n", encoding="utf-8")
            serena_dir = root / ".serena"
            serena_dir.mkdir()
            base = serena_dir / "project.yml"
            local = serena_dir / "project.local.yml"
            base.write_text("languages:\n- python\n", encoding="utf-8")
            local.write_text("languages:\n- python\n", encoding="utf-8")
            result = serena_safety.set_project_languages(root, apply=True)
            self.assertEqual(result["source"], "project.local.yml")
            self.assertEqual(serena_safety.parse_configured_languages(local.read_text(encoding="utf-8")), ["typescript"])
            self.assertEqual(serena_safety.parse_configured_languages(base.read_text(encoding="utf-8")), ["python"])

    def test_preserves_relevant_language_server_variant(self) -> None:
        configured = ["typescript_vts", "python_jedi"]
        self.assertEqual(
            serena_safety.preserve_language_variants(["typescript"], configured),
            ["typescript_vts"],
        )

    def test_parses_commented_language_list_and_preserves_comment(self) -> None:
        text = "languages:\n# Keep this project-specific note.\n- python\nencoding: utf-8\n"
        self.assertEqual(serena_safety.parse_configured_languages(text), ["python"])
        updated = serena_safety.replace_configured_languages(text, ["typescript"])
        self.assertIn("# Keep this project-specific note.", updated)
        self.assertEqual(serena_safety.parse_configured_languages(updated), ["typescript"])

    def test_parses_quoted_numeric_timeout(self) -> None:
        self.assertEqual(serena_safety.yaml_top_level_number('tool_timeout: "10"\n', "tool_timeout"), 10.0)

    def test_rejects_null_languages(self) -> None:
        with self.assertRaisesRegex(ValueError, "not null"):
            serena_safety.parse_configured_languages("languages: null\n")

    def test_removes_unsupported_project_timeout_on_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / ".serena" / "project.yml"
            path.parent.mkdir()
            path.write_text("languages: []\ntool_timeout: 10\n", encoding="utf-8")
            result = serena_safety.inspect_project_config(path, apply=True)
            self.assertEqual(result["status"], "removed-unsupported-key")
            self.assertNotIn("tool_timeout", path.read_text(encoding="utf-8"))

    def test_refuses_home_as_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve()
            with self.assertRaisesRegex(ValueError, "Refusing broad project audit"):
                serena_safety.validate_project_root(home, home)

    def test_refuses_write_outside_allowed_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            outside = Path(temp) / "outside.txt"
            root.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                serena_safety.safe_write_text(outside, "unsafe", root)

    def test_preserves_crlf_when_updating_agents(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "AGENTS.md"
            path.write_bytes(b"Header\r\n")
            serena_safety.update_agents(path, apply=True)
            content = path.read_bytes()
            self.assertIn(b"\r\n", content)
            self.assertNotIn(b"\n", content.replace(b"\r\n", b""))

    def test_wraps_invalid_yaml_as_value_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid YAML"):
            serena_safety.load_yaml_mapping("languages: [typescript\n")

    def test_restores_cross_file_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            existing = root / "existing.yml"
            created = root / "created.yml"
            existing.write_bytes(b"original\r\n")
            snapshots = serena_safety.capture_snapshots([existing, created])
            existing.write_bytes(b"changed\n")
            created.write_bytes(b"new\n")
            serena_safety.restore_snapshots(snapshots)
            self.assertEqual(existing.read_bytes(), b"original\r\n")
            self.assertFalse(created.exists())


if __name__ == "__main__":
    unittest.main()
