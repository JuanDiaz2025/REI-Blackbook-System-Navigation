#!/usr/bin/env python3
"""Diagnose why mastercdn.atm.gs fails in Playwright."""
import time
from playwright.sync_api import sync_playwright

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"

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
                # Trust proxy CA
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
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

        cdn_ok = []
        cdn_fail = []

        def on_resp(r):
            if "mastercdn" in r.url:
                cdn_ok.append(f"  {r.status}: {r.url[:80]}")

        def on_fail(r):
            if "mastercdn" in r.url:
                cdn_fail.append(f"  ERR ({r.failure}): {r.url[:80]}")

        page.on("response", on_resp)
        page.on("requestfailed", on_fail)

        print("Loading dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(5)

        print(f"\nCDN OK ({len(cdn_ok)}):")
        for u in cdn_ok[:10]:
            print(u)
        print(f"\nCDN FAILED ({len(cdn_fail)}):")
        for u in cdn_fail[:10]:
            print(u)

        # Also test a direct CDN fetch from the page context
        result = page.evaluate("""async () => {
            try {
                const r = await fetch('https://mastercdn.atm.gs/reibb.json');
                return { status: r.status, ok: r.ok };
            } catch(e) {
                return { error: e.message };
            }
        }""")
        print(f"\nPage fetch() test: {result}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
