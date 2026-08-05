#!/usr/bin/env python3
"""Audit or install Serena safety guidance and native timeout settings."""

from __future__ import annotations

import argparse
from collections import Counter
from io import StringIO
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML, YAMLError


START = "<!-- SERENA-PLAYBOOK:START -->"
END = "<!-- SERENA-PLAYBOOK:END -->"
PLAYBOOK = f"""{START}
## Serena Safety Playbook

- Never run broad Serena file or content searches over a user home, broad project root, generated tree, or binary directory.
- Restrict each Serena request to one known file or the smallest specific subdirectory and one concrete symbol or pattern.
- Expand scope incrementally and sequentially; never launch multiple broad Serena searches in parallel.
- Prefer `get_symbols_overview`, then retrieve only the required symbol body and the smallest useful response context.
- After a timeout, retry once with a narrower request. If it times out again, use the local Serena CLI from the workspace.
- If the Serena MCP process remains wedged, stop the stale `serena ... start-mcp-server` process and restart the MCP client before resuming.
{END}
"""

LANGUAGE_EXTENSIONS = {
    "al": {".al"},
    "bash": {".bash", ".sh"},
    "clojure": {".clj", ".cljc", ".cljs"},
    "cpp": {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"},
    "crystal": {".cr"},
    "csharp": {".cs"},
    "dart": {".dart"},
    "elixir": {".ex", ".exs"},
    "elm": {".elm"},
    "erlang": {".erl", ".hrl"},
    "fortran": {".f", ".f03", ".f08", ".f90", ".f95", ".for"},
    "fsharp": {".fs", ".fsi", ".fsx"},
    "go": {".go"},
    "groovy": {".gradle", ".groovy"},
    "haskell": {".hs", ".lhs"},
    "haxe": {".hx"},
    "java": {".java"},
    "julia": {".jl"},
    "kotlin": {".kt", ".kts"},
    "lua": {".lua"},
    "nix": {".nix"},
    "ocaml": {".ml", ".mli"},
    "pascal": {".pas", ".pp"},
    "perl": {".pl", ".pm"},
    "php": {".php"},
    "powershell": {".ps1", ".psd1", ".psm1"},
    "python": {".py", ".pyi"},
    "r": {".r"},
    "rego": {".rego"},
    "ruby": {".rb"},
    "rust": {".rs"},
    "scala": {".scala", ".sc"},
    "solidity": {".sol"},
    "svelte": {".svelte"},
    "swift": {".swift"},
    "systemverilog": {".sv", ".svh", ".v", ".vh"},
    "terraform": {".tf"},
    "typescript": {".cjs", ".cts", ".js", ".jsx", ".mjs", ".mts", ".ts", ".tsx"},
    "vue": {".vue"},
    "zig": {".zig"},
}
EXTENSION_LANGUAGE = {
    extension: language
    for language, extensions in LANGUAGE_EXTENSIONS.items()
    for extension in extensions
}
EXCLUDED_DIR_NAMES = {
    ".agents",
    ".dart_tool",
    ".claude",
    ".codex",
    ".git",
    ".hg",
    ".next",
    ".nuxt",
    ".opencode",
    ".serena",
    ".svn",
    ".svelte-kit",
    ".terraform",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "generated",
    "node_modules",
    "out",
    "target",
    "third_party",
    "vendor",
    "venv",
}
MIN_LANGUAGE_FILES = 5
MIN_LANGUAGE_SHARE = 0.10
PROCESS_TIMEOUT_SECONDS = 10
MAX_FALLBACK_FILES = 100_000
APPLY_FAILURE_STATUSES = {
    "initialization-error",
    "languages-key-missing",
    "missing",
    "missing-init-required",
    "missing-serena-cli",
    "parse-error",
}
LANGUAGE_VARIANT_BASE = {
    "cpp_ccls": "cpp",
    "csharp_omnisharp": "csharp",
    "php_phpactor": "php",
    "python_jedi": "python",
    "python_ty": "python",
    "ruby_solargraph": "ruby",
    "typescript_vts": "typescript",
}


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def preserve_newlines(original: str, updated: str) -> str:
    return updated.replace("\r\n", "\n").replace("\n", "\r\n") if "\r\n" in original else updated


def safe_write_text(path: Path, text: str, allowed_root: Path) -> None:
    root = allowed_root.resolve()
    if path.is_symlink():
        raise ValueError(f"Refusing to write through symlink: {path}")
    target = path.resolve(strict=False)
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError(f"Refusing to write outside {root}: {target}") from error
    if path.exists() and not path.is_file():
        raise ValueError(f"Refusing to replace non-file path: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def load_yaml_mapping(text: str) -> tuple[YAML, Any]:
    yaml = YAML(typ="rt")
    try:
        data = yaml.load(text)
    except YAMLError as error:
        raise ValueError(f"Invalid YAML: {error}") from error
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("Expected a top-level YAML mapping")
    return yaml, data


def replace_yaml_value(text: str, key: str, value: Any) -> str:
    yaml, data = load_yaml_mapping(text)
    data[key] = value
    output = StringIO()
    yaml.dump(data, output)
    return output.getvalue()


def has_equivalent_guidance(text: str) -> bool:
    lower = text.lower()
    scope_rule = "serena" in lower and any(
        phrase in lower
        for phrase in ("broad serena", "breite serena", "narrowly scoped", "kleinste spezifische")
    )
    expansion_rule = any(phrase in lower for phrase in ("incrementally", "sequentially", "inkrementell", "sequenziell"))
    fallback_rule = "timeout" in lower and "cli" in lower
    return scope_rule and expansion_rule and fallback_rule


def update_agents(path: Path, apply: bool, allowed_root: Path | None = None) -> dict[str, Any]:
    text = read_text(path)
    if START in text and END in text:
        updated = re.sub(
            rf"{re.escape(START)}.*?{re.escape(END)}\s*",
            PLAYBOOK,
            text,
            count=1,
            flags=re.DOTALL,
        )
        status = "managed-current" if updated == text else "managed-update-needed"
    elif has_equivalent_guidance(text):
        updated = text
        status = "equivalent-existing"
    else:
        prefix = text.rstrip()
        updated = f"{prefix}\n\n{PLAYBOOK}" if prefix else PLAYBOOK
        status = "missing"

    changed = updated != text
    if apply and changed:
        safe_write_text(path, preserve_newlines(text, updated), allowed_root or path.parent)
        status = "written"
    return {"path": str(path), "status": status, "changed": bool(apply and changed)}


def yaml_top_level_number(text: str, key: str) -> float | None:
    _, data = load_yaml_mapping(text)
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"Expected numeric YAML value for {key}")
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"Expected numeric YAML value for {key}") from error


def set_global_timeout(config: Path, apply: bool) -> dict[str, Any]:
    initialized = False
    if not config.is_file() and apply:
        serena = shutil.which("serena")
        if not serena:
            return {"path": str(config), "status": "missing-serena-cli", "value": None, "changed": False}
        expected_home = Path.home().resolve()
        requested_home = config.parent.parent.resolve()
        if requested_home != expected_home:
            return {"path": str(config), "status": "missing-init-required", "value": None, "changed": False}
        env = os.environ.copy()
        try:
            subprocess.run([serena, "init"], check=True, env=env, timeout=PROCESS_TIMEOUT_SECONDS)
        except (subprocess.SubprocessError, OSError) as error:
            return {"path": str(config), "status": "initialization-error", "error": str(error), "changed": False}
        initialized = True

    text = read_text(config)
    try:
        value = yaml_top_level_number(text, "tool_timeout")
    except ValueError as error:
        return {"path": str(config), "status": "parse-error", "error": str(error), "changed": False}
    if not text:
        return {"path": str(config), "status": "missing", "value": None, "changed": False}
    if value == 10.0:
        return {"path": str(config), "status": "current", "value": value, "changed": initialized}

    updated = replace_yaml_value(text, "tool_timeout", 10.0)
    if apply:
        safe_write_text(config, preserve_newlines(text, updated), config.parent.parent)
        value = 10.0
    return {
        "path": str(config),
        "status": "written" if apply else "update-needed",
        "value": value,
        "changed": apply,
    }


def inspect_project_config(path: Path, apply: bool = False) -> dict[str, Any]:
    text = read_text(path)
    try:
        value = yaml_top_level_number(text, "tool_timeout") if text else None
    except ValueError as error:
        return {"path": str(path), "exists": path.is_file(), "status": "parse-error", "error": str(error)}
    if apply and value is not None:
        yaml, data = load_yaml_mapping(text)
        del data["tool_timeout"]
        output = StringIO()
        yaml.dump(data, output)
        safe_write_text(path, preserve_newlines(text, output.getvalue()), path.parent.parent)
        return {
            "path": str(path),
            "exists": True,
            "unsupported_tool_timeout": None,
            "status": "removed-unsupported-key",
        }
    return {
        "path": str(path),
        "exists": path.is_file(),
        "unsupported_tool_timeout": value,
        "status": "unsupported-key" if value is not None else "ok",
    }


def is_project_source(path: Path) -> bool:
    return not any(part.lower() in EXCLUDED_DIR_NAMES for part in path.parts)


def project_files(cwd: Path) -> list[Path]:
    git = shutil.which("git")
    if git:
        try:
            result = subprocess.run(
                [git, "-C", str(cwd), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
                check=False,
                capture_output=True,
                timeout=PROCESS_TIMEOUT_SECONDS,
            )
            if result.returncode == 0:
                paths = [Path(os.fsdecode(raw)) for raw in result.stdout.split(b"\0") if raw]
                return [path for path in paths if is_project_source(path) and (cwd / path).is_file()]
        except subprocess.TimeoutExpired:
            pass

    files: list[Path] = []
    deadline = time.monotonic() + PROCESS_TIMEOUT_SECONDS
    for root, dir_names, file_names in os.walk(cwd):
        if time.monotonic() > deadline:
            raise RuntimeError(f"Filesystem language scan exceeded {PROCESS_TIMEOUT_SECONDS} seconds")
        dir_names[:] = [name for name in dir_names if name.lower() not in EXCLUDED_DIR_NAMES]
        root_path = Path(root)
        for file_name in file_names:
            relative = (root_path / file_name).relative_to(cwd)
            if is_project_source(relative):
                files.append(relative)
                if len(files) > MAX_FALLBACK_FILES:
                    raise RuntimeError(f"Refusing to inspect more than {MAX_FALLBACK_FILES} files")
    return files


def count_project_languages(cwd: Path) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for path in project_files(cwd):
        language = EXTENSION_LANGUAGE.get(path.suffix.lower())
        if language:
            counts[language] += 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def detect_project_languages(cwd: Path) -> dict[str, int]:
    counts = count_project_languages(cwd)
    return select_project_languages(counts)


def select_project_languages(counts: dict[str, int]) -> dict[str, int]:
    if not counts:
        return {}
    total = sum(counts.values())
    primary = next(iter(counts))
    return {
        language: count
        for language, count in counts.items()
        if language == primary or count >= MIN_LANGUAGE_FILES or count / total >= MIN_LANGUAGE_SHARE
    }


def parse_configured_languages(text: str) -> list[str] | None:
    _, data = load_yaml_mapping(text)
    if "languages" not in data:
        return None
    languages = data["languages"]
    if languages is None:
        raise ValueError("languages must be a list, not null")
    if not isinstance(languages, list) or not all(isinstance(language, str) for language in languages):
        raise ValueError("languages must be a list of strings")
    return list(languages)


def replace_configured_languages(text: str, languages: list[str]) -> str:
    return replace_yaml_value(text, "languages", languages)


def preserve_language_variants(base_languages: list[str], configured: list[str] | None) -> list[str]:
    configured_variants = {
        LANGUAGE_VARIANT_BASE[language]: language
        for language in configured or []
        if language in LANGUAGE_VARIANT_BASE
    }
    return [configured_variants.get(language, language) for language in base_languages]


def set_project_languages(cwd: Path, apply: bool) -> dict[str, Any]:
    config = cwd / ".serena" / "project.yml"
    local_config = cwd / ".serena" / "project.local.yml"
    all_counts = count_project_languages(cwd)
    counts = select_project_languages(all_counts)
    detected_base = list(counts)

    if not config.is_file() and apply and detected_base:
        serena = shutil.which("serena")
        if not serena:
            return {
                "path": str(config),
                "status": "missing-serena-cli",
                "configured": None,
                "detected": detected_base,
                "counts": counts,
                "ignored_low_signal": {
                    language: count for language, count in all_counts.items() if language not in counts
                },
                "changed": False,
            }
        command = [serena, "project", "create", str(cwd)]
        for language in detected_base:
            command.extend(["--language", language])
        try:
            subprocess.run(command, check=True, timeout=PROCESS_TIMEOUT_SECONDS)
        except (subprocess.SubprocessError, OSError) as error:
            return {
                "path": str(config),
                "status": "initialization-error",
                "error": str(error),
                "configured": None,
                "detected": detected_base,
                "counts": counts,
                "changed": False,
            }

    text = read_text(config)
    local_text = read_text(local_config)
    try:
        local_languages = parse_configured_languages(local_text) if local_text else None
        base_languages = parse_configured_languages(text) if text else None
    except ValueError as error:
        return {
            "path": str(local_config if local_text else config),
            "status": "parse-error",
            "error": str(error),
            "detected": detected_base,
            "counts": counts,
            "changed": False,
        }
    effective_config = local_config if local_languages is not None else config
    effective_text = local_text if local_languages is not None else text
    configured = local_languages if local_languages is not None else base_languages
    detected = preserve_language_variants(detected_base, configured)
    if configured is None:
        status = "missing" if not text else "languages-key-missing"
    elif configured == detected:
        status = "current"
    else:
        status = "update-needed"

    changed = False
    if apply and effective_text and configured != detected:
        updated = replace_configured_languages(effective_text, detected)
        safe_write_text(effective_config, preserve_newlines(effective_text, updated), cwd)
        configured = detected
        status = "written"
        changed = True

    return {
        "path": str(effective_config),
        "base_path": str(config),
        "local_override_path": str(local_config),
        "source": "project.local.yml" if local_languages is not None else "project.yml",
        "status": status,
        "configured": configured,
        "detected": detected,
        "detected_base_languages": detected_base,
        "counts": counts,
        "ignored_low_signal": {language: count for language, count in all_counts.items() if language not in counts},
        "selection_threshold": {
            "minimum_files": MIN_LANGUAGE_FILES,
            "minimum_share": MIN_LANGUAGE_SHARE,
            "primary_language_always_included": True,
        },
        "excluded_directories": sorted(EXCLUDED_DIR_NAMES),
        "changed": changed,
    }


def inspect_client_config(path: Path, generated: bool = False) -> dict[str, Any]:
    text = read_text(path)
    serena = "serena" in text.lower()
    tool_timeout_10 = bool(
        re.search(r"--tool-timeout[\s\"',:=\-]+10(?:\.0)?(?:[\s\"',\]}]|$)", text, re.IGNORECASE)
    )
    client_timeout_10s = bool(
        re.search(r"(?i)(?:timeout|startup_timeout_sec)\s*[\"']?\s*[:=]\s*[\"']?(?:10000|10(?:\.0)?)\b", text)
    )
    return {
        "path": str(path),
        "exists": path.is_file(),
        "generated": generated,
        "inspection": "heuristic-only; confirm with the active client",
        "contains_serena": serena,
        "tool_timeout_10": tool_timeout_10 if serena else False,
        "client_timeout_10s": client_timeout_10s if serena else False,
    }


def candidate_client_paths(cwd: Path, home: Path) -> list[tuple[Path, bool]]:
    paths = [
        (cwd / ".agents" / "mcp.json", False),
        (cwd / ".agents" / "mcp_config.json", False),
        (cwd / ".mcp.json", False),
        (cwd / "opencode.json", False),
        (cwd / "opencode.jsonc", False),
        (cwd / ".opencode" / "opencode.jsonc", False),
        (home / ".agents" / "mcp.json", False),
        (home / ".agents" / "mcp_config.json", False),
        (home / ".config" / "mcp" / "servers.yaml", False),
        (home / ".config" / "opencode" / "opencode.jsonc", False),
        (home / ".codex" / "config.toml", False),
        (home / ".claude.json", False),
        (home / ".hermes" / "config.yaml", False),
        (home / ".config" / "mcp" / "generated" / "opencode-mcp.jsonc", True),
        (home / ".config" / "mcp" / "generated" / "codex-mcp.toml", True),
        (home / ".config" / "mcp" / "generated" / "claude-mcp.json", True),
        (home / ".config" / "mcp" / "generated" / "hermes-mcp.yaml", True),
    ]
    seen: set[Path] = set()
    return [(path, generated) for path, generated in paths if not (path in seen or seen.add(path))]


def validate_project_root(cwd: Path, home: Path) -> None:
    if cwd == home or cwd.parent == cwd:
        raise ValueError(f"Refusing broad project audit at user home or filesystem root: {cwd}")


def report_has_status(value: Any, statuses: set[str]) -> bool:
    if isinstance(value, dict):
        return value.get("status") in statuses or any(report_has_status(item, statuses) for item in value.values())
    if isinstance(value, list):
        return any(report_has_status(item, statuses) for item in value)
    return False


def managed_paths(cwd: Path, home: Path) -> list[Path]:
    return list(
        dict.fromkeys(
            [
                cwd / "AGENTS.md",
                home / "AGENTS.md",
                home / ".serena" / "serena_config.yml",
                cwd / ".serena" / "project.yml",
                cwd / ".serena" / "project.local.yml",
            ]
        )
    )


def capture_snapshots(paths: list[Path]) -> dict[Path, bytes | None]:
    snapshots: dict[Path, bytes | None] = {}
    for path in paths:
        if path.is_symlink():
            raise ValueError(f"Refusing to snapshot symlink: {path}")
        snapshots[path] = path.read_bytes() if path.is_file() else None
    return snapshots


def restore_snapshots(snapshots: dict[Path, bytes | None]) -> None:
    for path, content in snapshots.items():
        if path.is_symlink():
            raise ValueError(f"Refusing to restore through symlink: {path}")
        if content is None:
            if path.is_file():
                path.unlink()
            continue
        safe_write_text(path, content.decode("utf-8"), path.parent)


def build_report(cwd: Path, home: Path, apply: bool) -> dict[str, Any]:
    agents_paths = list(dict.fromkeys([cwd / "AGENTS.md", home / "AGENTS.md"]))
    global_config = home / ".serena" / "serena_config.yml"
    native_serena = {
        "global": set_global_timeout(global_config, apply),
        "languages": set_project_languages(cwd, apply),
        "project": [
            inspect_project_config(cwd / ".serena" / "project.yml", apply),
            inspect_project_config(cwd / ".serena" / "project.local.yml", apply),
        ],
        "precedence": "--tool-timeout CLI override > global serena_config.yml; project.yml has no tool_timeout field",
    }
    apply_agents = apply and not report_has_status(native_serena, {"parse-error", "initialization-error"})
    return {
        "mode": "apply" if apply else "audit",
        "native_serena": native_serena,
        "agents": [update_agents(path, apply_agents, cwd if path.parent == cwd else home) for path in agents_paths],
        "mcp_candidates": [
            inspect_client_config(path, generated)
            for path, generated in candidate_client_paths(cwd, home)
            if path.is_file()
        ],
        "next_action": "Identify the active MCP client/SSOT before editing client timeout values.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    cwd = args.cwd.expanduser().resolve()
    home = args.home.expanduser().resolve()
    try:
        validate_project_root(cwd, home)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    snapshots: dict[Path, bytes | None] | None = None
    try:
        preflight = build_report(cwd, home, False)
        if args.apply and report_has_status(preflight, {"parse-error"}):
            preflight["mode"] = "preflight-failed"
            print(json.dumps(preflight, indent=2, ensure_ascii=False))
            return 2
        if args.apply:
            snapshots = capture_snapshots(managed_paths(cwd, home))
            report = build_report(cwd, home, True)
            if report_has_status(report, APPLY_FAILURE_STATUSES):
                restore_snapshots(snapshots)
                report["mode"] = "apply-failed-rolled-back"
                report["rolled_back"] = True
            else:
                report["rolled_back"] = False
        else:
            report = preflight
    except (OSError, RuntimeError, ValueError) as error:
        if snapshots is not None:
            try:
                restore_snapshots(snapshots)
            except (OSError, ValueError) as rollback_error:
                print(
                    json.dumps(
                        {"mode": "failed-rollback-incomplete", "error": str(error), "rollback_error": str(rollback_error)},
                        indent=2,
                        ensure_ascii=False,
                    )
                )
                return 2
        print(json.dumps({"mode": "failed", "error": str(error)}, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 2 if report_has_status(report, APPLY_FAILURE_STATUSES) else 0


if __name__ == "__main__":
    raise SystemExit(main())
