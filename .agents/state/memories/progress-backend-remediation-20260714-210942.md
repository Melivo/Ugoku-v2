# Backend-Remediation Fortschritt

- Status: IMPL abgeschlossen; VERIFY läuft.
- Änderung: jsonc-parser als direkte Runtime-Abhängigkeit; OpenCode .jsonc wird JSONC-konform gelesen und mit gezielten mcp-Edits geschrieben.
- Regression: kommentierte OpenCode-JSONC mit fremdem MCP-Eintrag synchronisiert alle drei Office-MCPs; Kommentare und Fremdeintrag bleiben erhalten.
- Fokus-Test: PASS (1 Datei, 36 Tests).
- Scope: Keine Serena-Änderung; AnythingLLM-Writer bleibt unverändert.
