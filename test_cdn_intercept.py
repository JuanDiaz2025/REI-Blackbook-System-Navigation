#!/usr/bin/env python3
"""Test CDN route interception rendering."""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import cdn_cache

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
                "--proxy-server=direct://",
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
        cdn_cache.install_routes(ctx)
        page = ctx.new_page()
        page.set_default_timeout(60000)

        cdn_ok = []
        cdn_fail = []
        page.on("response", lambda r: cdn_ok.append(r.url[:80]) if "mastercdn" in r.url else None)
        page.on("requestfailed", lambda r: cdn_fail.append(f"{r.url[:80]} ({r.failure})") if "mastercdn" in r.url else None)

        print("Loading dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(6)

        info = page.evaluate("""() => {
            const body = document.body;
            const cs = window.getComputedStyle(body);
            const nav = document.querySelector('nav, .sidebar, [class*="sidebar"], [class*="navbar"]');
            const navCs = nav ? window.getComputedStyle(nav) : null;
            const navBg = navCs ? navCs.backgroundColor : null;
            const firstStyled = document.querySelector('[class*="nav"], [class*="menu"], [class*="side"]');
            const firstCs = firstStyled ? window.getComputedStyle(firstStyled) : null;
            return {
                bodyBg: cs.backgroundColor,
                bodyFont: cs.fontFamily,
                bodyColor: cs.color,
                stylesheets: document.styleSheets.length,
                navBg,
                navClass: nav ? nav.className : null,
                firstStyledBg: firstCs ? firstCs.backgroundColor : null,
                firstStyledClass: firstStyled ? firstStyled.className : null,
                title: document.title,
                url: window.location.href,
            };
        }""")
        print("Page rendering info:")
        print(json.dumps(info, indent=2))
        print(f"\nCDN OK: {len(cdn_ok)}")
        print(f"CDN FAIL: {len(cdn_fail)}")
        for f in cdn_fail[:5]:
            print(f"  FAIL: {f}")

        shot = SCREENSHOTS / "cdn_intercept_test.png"
        page.screenshot(path=str(shot), full_page=False)
        print(f"\nScreenshot: {shot}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
