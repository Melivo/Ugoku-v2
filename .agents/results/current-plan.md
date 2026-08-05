# Current /work Plan

Source: `docs/plans/work/010-pros-api-bridge-remaining-slices.md`

Session: 2026-05-26 API Bridge Remaining Slices

Status: Completed

## Active Priority Tier

| Task | Agent | Priority | Status | Dependencies |
|---|---|---|---|---|
| 4. Microsoft OAuth Token Exchange ohne `offline_access` implementieren | Backend | P0 | DONE | 3 DONE |
| 5. Microsoft OAuth Logout/Local Credential Delete implementieren | Backend/Security | P0 | DONE | 4 DONE |
| 6. `offline_access`, Refresh Token Storage und Refresh Flow nur nach Revocation-Support aktivieren | Backend/Security | P0 | DONE | 5 DONE |
| 7. Microsoft Graph read-only Client und redacted Status implementieren | Backend | P0 | DONE | 4, 6 DONE |
| 8. Graph Mail/Calendar/Files Read Kommandos implementieren | Backend | P0 | DONE | 7 DONE |
| 9. Graph Excel readRange fuer `.xlsx` DriveItems implementieren | Backend | P1 | DONE | 7 DONE |
| 10. DOCX Inspect/Extract read-only Adapter implementieren | Backend | P0 | DONE | 2 DONE |
| 11. DOCX PlanEdit/ApplyApprovedEdit mit Preview, Approval und Backup implementieren | Backend/Security | P1 | DONE | 10 DONE |
| 12. PPTX Inspect/Extract read-only Adapter implementieren | Backend | P1 | DONE | 2, 7 DONE |
| 13. PPTX Text Replacement Preview und Approved Apply implementieren | Backend/Security | P2 | DONE | 12 DONE |
| 14. QNAP MCP Assistant Security/Quality Review durchfuehren | QA/Security | P0 | DONE | 1 DONE |
| 15. QNAP File Station Fallback spezifizieren, falls MCP Assistant nicht validiert wird | Backend/Security | P1 | DONE | 14 DONE |
| 16. QNAP Browse/Search und Transfer Preview/Approval implementieren | Backend | P1 | DONE | 15 DONE |
| 17. Endnutzer-, Admin- und Credential-Dokumentation aktualisieren | Docs/PM | P1 | DONE | 4, 10, 14 DONE |
| 18. API Bridge Security Review und Regressionstest-Suite abschliessen | QA/Security | P0 | DONE | 6, 11, 16 DONE |
| 19. ShipGate ausfuehren und Plan 009/010 Status synchronisieren | QA | P0 | DONE | 18, 20 DONE |
| 20. CLI Command Dokumentation fuer MCP-Funktionen und Server schreiben | Docs/PM | P1 | DONE | 17 DONE |

## Completion Summary

- Plan 010 completed on 2026-05-29.
- Security Review: passed with no Critical/High findings.
- ShipGate: passed.
- Remaining residual risks are live Microsoft tenant validation and live QNAP NAS/admin-pilot validation; bridges are not marked broadly `validated`.

## Acceptance Criteria

- `python scripts/generate-pros-hilfe.py`: passed with `wkhtmltopdf`.
- `npm run typecheck`: passed.
- `npm run lint`: passed.
- `node scripts/validate-runtime-files.js`: passed with known `MODULE_TYPELESS_PACKAGE_JSON` warning.
- `npm run test`: passed, 109 passed and 1 skipped.
- `npm run release:dry-run`: passed.
- `npm audit --audit-level=moderate`: passed, 0 vulnerabilities.
- `git diff --check`: passed with known CRLF warnings only.
