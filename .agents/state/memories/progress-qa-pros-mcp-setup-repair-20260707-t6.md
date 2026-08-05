# Fortschritt P0 Task 6 – QNAP Credential-/MCP-Tests erweitern

Session: pros-mcp-setup-repair-20260707
Status: gestartet

Scope:
- packages/pros-cli/src/cli.test.ts
- packages/pros-cli/src/mcp-client-config.test.ts
- packages/pros-cli/src/mcp-qnap-assistant.test.ts
- ggf. direkt relevante Credential-Store-Tests

Leitplanken:
- Keine Secrets.
- Kein Commit.
- ZIP/Init, Microsoft Graph, Docs nicht bearbeiten.
- Produktionscode nur bei eindeutigem Testblocker/Finding; ansonsten dokumentieren.

Nächste Schritte:
1. T5-bezogene Änderungen und bestehende Testabdeckung mit Serena analysieren.
2. Fehlende Akzeptanzkriterien identifizieren.
3. Scoped Tests und ggf. Biome/Typecheck ausführen.
4. Ergebnis in `.agents/results/result-qa-pros-mcp-setup-repair-20260707-t6.md` und Serena Memory schreiben.
