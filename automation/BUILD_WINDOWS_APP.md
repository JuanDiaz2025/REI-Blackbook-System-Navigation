# Getting the app onto your Windows PC

Two ways — start with **A** (works immediately), move to **B** when you want a
single icon with no Python visible.

## A. Run it now (double-click launcher)

1. Install **Python 3** once: https://www.python.org/downloads/
   → on the first screen, tick **"Add python.exe to PATH"**, then Install.
2. Download this `automation` folder from the repo
   (`juandiaz2025/rei-blackbook-system-navigation`, branch
   `claude/rei-login-access-nzdp6n`) — use GitHub's **Code ▸ Download ZIP** and
   unzip it.
3. Double-click **`run.bat`**.
   The first run installs components, then the app opens in your browser at
   `http://127.0.0.1:5000`. That window *is* the app — leave `run.bat` open
   while you use it.

## B. Turn it into a single `.exe` (no Python window)

On any Windows PC with Python installed:

```bat
cd automation
python -m pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --onefile --name PostVisitDebrief ^
  --add-data "ui;ui" ^
  --collect-all google_auth_oauthlib --collect-all googleapiclient ^
  app.py
```

The result is `dist\PostVisitDebrief.exe` — copy it anywhere and double-click.
(Config and the REI session are saved next to the .exe.)

> Windows SmartScreen may warn the first time because the .exe isn't
> code-signed. Choose **More info ▸ Run anyway**. Proper signing (removes the
> warning) needs a code-signing certificate and can be added later.

## First-time setup inside the app

1. **Setup** card → paste your keys (REI login, Voicenotes token, Anthropic key,
   Google OAuth client file path, escalation email) → **Save setup**.
2. **REI BlackBook connection** → **Log in**. If it asks, paste the verification
   link REI emails you → **Complete login**.
3. **Process completed visits** → keep **Preview only** on for the first run to
   see the drafts, then untick it to post to REI for real.
