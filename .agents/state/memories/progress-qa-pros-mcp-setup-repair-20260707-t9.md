# Startstatus QA Smoke-Run Task 9

Session: pros-mcp-setup-repair-20260707
Task: P1 Task 9 - End-to-end Smoke-Run definieren und ausführen
Status: gestartet
Zeitpunkt: 2026-07-07

Scope:
- Windows `pros init` / ZIP extraction in Workspace-Pfad mit Leerzeichen
- Microsoft Graph Setup-Status / missing client id / redirect config ohne echte Secrets
- QNAP token status / empty stdin / credential target semantics ohne Token-Leakage
- HubSpot credential/status/config guidance ohne echte Secrets
- MCP config dry-runs/status für OpenCode und AnythingLLM mit No-Secret-Invariante

Guardrails:
- Keine echten Tokens/Secrets ausgeben oder erfinden
- Keine Produktionscode-Änderungen
- Ergebnisse unter `.agents/results/` dokumentieren
- Externe Credential-Flows bei fehlenden echten Zugangsdaten als not-run/external prerequisite markieren und durch deterministische lokale Dry-Run-/Status-Evidenz ersetzen
