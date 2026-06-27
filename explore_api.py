#!/usr/bin/env python3
"""Explore the contacts API to understand its structure."""
import json, time
from playwright.sync_api import sync_playwright
import cdn_cache

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/opt/pw-browsers/chromium",
            args=["--no-sandbox","--disable-dev-shm-usage","--proxy-server=direct://",
                  "--disable-features=ThirdPartyCookieBlocking,BlockThirdPartyCookies"],
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            storage_state=SESSION_FILE, ignore_https_errors=True,
        )
        cdn_cache.install_routes(ctx)
        page = ctx.new_page()
        page.set_default_timeout(60000)

        # Load site to establish auth context
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(3)

        # Try various API endpoints and params
        apis = [
            "/api/contacts?page=1&limit=5",
            "/api/contacts?page=1&per_page=5",
            "/api/contacts?offset=0&limit=5",
            "/api/contacts/list?page=1&limit=5",
        ]

        for api in apis:
            result = page.evaluate(f"""async () => {{
                const r = await fetch('{api}', {{credentials: 'include', headers: {{'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}}}});
                const text = await r.text();
                return {{ status: r.status, preview: text.slice(0, 800), length: text.length }};
            }}""")
            print(f"\n=== {api} ===")
            print(f"Status: {result['status']}, Length: {result['length']}")
            print(result['preview'])

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
