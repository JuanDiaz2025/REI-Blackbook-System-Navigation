# REI-Blackbook-System-Navigation
AI Controls

## REI Blackbook login check

Automates logging into REI Blackbook and pauses for a manually-entered
verification code, so it only ever triggers one code per run.

```bash
cp .env.example .env   # fill in REI_LOGIN_URL / REI_EMAIL / REI_PASSWORD
npm install
npm run login           # logs in, waits for you to paste the emailed code
npm run check-access    # reuses the saved session to confirm access later
```

Notes:
- Credentials live only in your local `.env` (already gitignored) — never commit them.
- `npm run login` opens a real browser (set `HEADLESS=true` to run headless) and writes
  step-by-step screenshots to `screenshots/` for debugging.
- The login form selectors in `scripts/rei-login.js` are best-effort; adjust them if the
  real page markup differs once you inspect the screenshots.
- A successful login saves the session to `auth.json` (gitignored) so `check-access.js`
  doesn't need to log in — and doesn't request another code — every time.
