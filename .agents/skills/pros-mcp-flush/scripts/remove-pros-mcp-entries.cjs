#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const { applyEdits, modify, parse, printParseErrorCode } = require("jsonc-parser");

const PROS_KEYS = [
  "hubspot",
  "microsoft-graph",
  "qnap-mcp-assistant",
  "docx-local",
  "excel-local",
  "powerpoint-local",
  "pros-mcp-hubspot-remote",
  "pros-mcp-microsoft-graph",
  "pros-mcp-qnap-assistant",
  "pros-mcp-qnap-files",
  "qnap-mcp-files",
  "pros-mcp-docx-local",
  "pros-mcp-office-files",
  "office-files",
];

const PROS_COMMANDS = new Set([
  "pros-mcp-hubspot-remote",
  "mcp-microsoft-graph",
  "pros-mcp-microsoft-graph",
  "pros-mcp-qnap-assistant",
  "pros-mcp-qnap-files",
  "mcp-docx-local",
  "pros-mcp-docx-local",
  "mcp-excel-local",
  "mcp-powerpoint-local",
  "pros-mcp-office-files",
]);

function argument(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

function cleanConfig(filePath, containerKey, dryRun) {
  if (!filePath || !fs.existsSync(filePath)) {
    return { path: filePath, status: "missing", removed: [] };
  }

  let content = fs.readFileSync(filePath, "utf8");
  const errors = [];
  const document = parse(content, errors, { allowTrailingComma: true });
  if (errors.length > 0) {
    const error = errors[0];
    throw new Error(
      `${filePath}: ${printParseErrorCode(error.error)} at offset ${error.offset}`,
    );
  }

  const container = document?.[containerKey];
  const removed = Object.entries(container ?? {})
    .filter(([key, entry]) => {
      if (PROS_KEYS.includes(key)) return true;
      const command = entry?.command;
      const executable = Array.isArray(command) ? command[0] : command;
      return typeof executable === "string" && PROS_COMMANDS.has(executable);
    })
    .map(([key]) => key);

  for (const key of removed) {
    content = applyEdits(
      content,
      modify(content, [containerKey, key], undefined, {
        formattingOptions: { insertSpaces: true, tabSize: 2, eol: "\n" },
      }),
    );
  }

  if (!dryRun && removed.length > 0) {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content.endsWith("\n") ? content : `${content}\n`, "utf8");
  }

  return { path: filePath, status: "ok", removed };
}

try {
  const dryRun = process.argv.includes("--dry-run");
  const result = {
    dryRun,
    opencode: cleanConfig(argument("--opencode"), "mcp", dryRun),
    anythingllm: cleanConfig(argument("--anythingllm"), "mcpServers", dryRun),
  };
  process.stdout.write(`${JSON.stringify(result)}\n`);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 1;
}
