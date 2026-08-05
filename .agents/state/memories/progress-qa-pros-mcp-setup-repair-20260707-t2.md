# Progress QA – pros-mcp-setup-repair-20260707 T2

Status: gestartet

Aufgabe: P0 Task 2 – Init-/Zip-Regressionstests erweitern.

Scope:
- `packages/pros-cli/src/zip.test.ts`
- relevante `packages/pros-cli/src/init*.test.ts`
- minimale test-only Fixtures falls nötig

Leitplanken:
- Keine Secrets.
- Kein Commit.
- Produktionscode nur bei eindeutigem Testblocker anfassen; sonst als Finding dokumentieren.
- Nicht bearbeiten: Microsoft Graph, QNAP, Docs.

Nächste Schritte:
1. ZIP-/Init-Testabdeckung per Serena analysieren.
2. Fehlende Regressionstests minimal ergänzen oder vorhandene Abdeckung bestätigen.
3. Scoped Tests und, falls möglich, Typecheck/Lint ausführen.
4. Ergebnis in `.agents/results/result-qa-pros-mcp-setup-repair-20260707-t2.md` und Serena Memory schreiben.
