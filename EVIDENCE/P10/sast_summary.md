## Gitleaks
- Initial local scan (working tree, --no-git) flagged `.env` with JWT_SECRET_KEY.
- Fix: `.env` kept local only (not in repo), use `.env.example` for template; evidence regenerated.
- Result: `EVIDENCE/P10/gitleaks.json` is empty (`[]`).
