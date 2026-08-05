# Final QA Review – pros-mcp-setup-repair-20260707

Session: `pros-mcp-setup-repair-20260707`
Task: Step 6 final QA review all deliverables
Status: WARNING

## Review Result: WARNING

Keine CRITICAL- oder HIGH-Issues verifiziert. Zwei MEDIUM-Dokumentations-/Secret-Handling-Findings erfordern vor Ship eine kurze Remediation. Weitere LOW-Findings sind nicht release-blockierend, sollten aber mitbereinigt werden.

### CRITICAL
- Keine verifizierten Findings.

### HIGH
- Keine verifizierten Findings.

### MEDIUM
- `README.md:164` — Die HubSpot-Anleitung liest `Client Secret` mit `Read-Host` ohne Maskierung. Das schreibt das Secret zwar nicht in argv/History, kann es aber sichtbar im Terminal/Screen-Recording/Transcript-Kontext exponieren und widerspricht dem redaktionell sicheren Setup-Ziel. — Remediation:
  ```powershell
  $hubspotSecret = Read-Host "HubSpot client secret" -MaskInput
  try {
    $hubspotSecret | pros mcp hubspot credentials set --client-id $hubspotClientId --client-secret-stdin
  }
  finally {
    Remove-Variable hubspotSecret -ErrorAction SilentlyContinue
  }
  ```
- `README.md:188` — Der Microsoft-Graph-Abschnitt nennt als lokalen Startbefehl `pros-mcp-microsoft-graph`, waehrend `packages/pros-cli/package.json:9`, `packages/pros-cli/src/mcp-client-config.ts:827` und die synchronisierten Runtime-/CLI-Dokumente `mcp-microsoft-graph` verwenden. Das kann manuelle MCP-Reparaturen auf einen nicht vorhandenen Binary-Namen lenken. — Remediation:
  ```md
  Der sichtbare MCP-Servername ist `microsoft-graph`; der lokale Startbefehl ist `mcp-microsoft-graph`.
  ```

### LOW
- `docs/plans/work/026-pros-mcp-setup-repair.md:45` — Der Plantracker markiert Tasks 1–7 weiterhin als `TODO`, obwohl die Ergebnisartefakte T1–T7 abgeschlossen/pass melden; die Done-When-Checkboxen bleiben ebenfalls offen. Remediation: Tasks 1–7 auf `DONE` setzen, Done-When-Checkboxen nach vorhandener T9/T10-Evidenz abhaken und Status auf final-review/remediation aktualisieren.
- `packages/pros-cli/src/mcp-client-config.ts:577` — Der Secret-Scan-Check verwendet dieselbe Message auch im Fehlerfall (`No obvious secret value found...`). Bei einem negativen Check erscheint dadurch eine widerspruechliche Diagnose. Remediation: `hasSecretLikeValue(config)` einmal berechnen und bei `hasSecret` eine Warnmessage ausgeben.

## Verification commands / evidence

- `npm audit --audit-level=moderate` — PASS, 0 vulnerabilities.
- `npm run lint --if-present` — PASS, Biome checked 68 files.
- `npm run typecheck --if-present` — PASS.
- `npm test && npm run build` — PASS, 27 test files, 213 passed, 1 skipped; build PASS.
- `npm run release:dry-run` — PASS, version `0.5.30`, tag `pros-v0.5.30`.
- `git diff --check` — PASS; only LF/CRLF warnings.
- `npm test -- --runInBand` — not applicable; Vitest rejects Jest option `--runInBand`, corrected by running `npm test`.
- Serena MCP: symbol overviews and targeted symbol reads for changed source files; diagnostics for `zip.ts`, `microsoft-oauth.ts`, `microsoft-graph.ts`, `cli.ts`, `mcp-client-config.ts`, `mcp-qnap-assistant.ts` returned no errors/warnings.
- Serena memories/results reviewed: plan, root-cause report, T1–T10 result memories/files including T9 smoke and T10 release/rollback evidence.

## Acceptance criteria checklist

- [x] All scoped source, test, docs, runtime workflow, plan, and result artifacts reviewed.
- [x] Security reviewed: secret leakage, unsafe archive extraction, credential target confusion, OAuth misclassification, config secret scan.
- [x] Performance/reliability reviewed: temp extraction cleanup, repeated status checks, config scan behavior, smoke coverage.
- [x] Accessibility/docs usability reviewed: Windows/PowerShell instructions, redirect guidance, stdin behavior, redaction-safe troubleshooting.
- [x] Code quality reviewed: minimality, tests, TypeScript diagnostics, lint/typecheck/build/test evidence, no source edits by QA.
- [x] Findings include severity, file:line, description, and remediation.
- [x] No CRITICAL/HIGH findings found.

## Step 7 remediation required?

Yes. Required before final ship for the two MEDIUM docs findings: mask the HubSpot secret prompt and correct the README Microsoft Graph local binary name. LOW cleanup can be included in the same remediation pass.
