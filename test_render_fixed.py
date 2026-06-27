#!/usr/bin/env python3
"""Quick test: load session, capture dashboard with full CSS rendering."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"
SCREENSHOTS = Path("/home/user/REI-Blackbook-System-Navigation/screenshots")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/opt/pw-browsers/chromium",
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--proxy-server=http://127.0.0.1:39363",
                "--proxy-bypass-list=my.reiblackbook.com,*.reiblackbook.com,auth.automatedgenius.com,*.automatedgenius.com",
                "--disable-features=ThirdPartyCookieBlocking,BlockThirdPartyCookies",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            storage_state=SESSION_FILE,
            ignore_https_errors=True,
        )
        page = ctx.new_page()
        page.set_default_timeout(60000)

        failed = []
        cdn_loaded = []
        page.on("response", lambda r: cdn_loaded.append(r.url) if "mastercdn" in r.url and r.status < 400 else None)
        page.on("requestfailed", lambda r: failed.append(r.url) if "mastercdn" in r.url else None)

        print("Loading dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(8)

        # Check rendering
        info = page.evaluate("""() => {
            const body = document.body;
            const cs = window.getComputedStyle(body);
            const nav = document.querySelector('nav, .sidebar, [class*="sidebar"], [class*="navbar"]');
            const navCs = nav ? window.getComputedStyle(nav) : null;
            return {
                bodyBg: cs.backgroundColor,
                bodyFont: cs.fontFamily,
                stylesheets: document.styleSheets.length,
                navBg: navCs ? navCs.backgroundColor : null,
                navClass: nav ? nav.className : null,
                title: document.title,
            };
        }""")
        print("Page info:", json.dumps(info, indent=2))
        print(f"CDN assets loaded: {len(cdn_loaded)}")
        print(f"CDN assets failed: {len(failed)}")
        if failed:
            for f in failed[:5]:
                print(f"  FAIL: {f}")

        shot = SCREENSHOTS / "render_fixed_dashboard.png"
        page.screenshot(path=str(shot), full_page=False)
        print(f"Screenshot: {shot}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
