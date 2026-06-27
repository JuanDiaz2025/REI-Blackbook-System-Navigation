#!/usr/bin/env python3
"""Open one contact detail page and extract all available information."""
import json, time
from playwright.sync_api import sync_playwright
import cdn_cache

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"

# First contact from our list: Michael Tostado, id=20466744
CONTACT_ID = "20466744"
CONTACT_URL = f"https://my.reiblackbook.com/contacts/{CONTACT_ID}"

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

        # Capture API calls made by the contact detail page
        api_calls = []
        def on_request(r):
            if "reiblackbook.com" in r.url and any(x in r.url for x in ['/api/', '/profitdial/', '/services/']):
                api_calls.append({"method": r.method, "url": r.url})

        page.on("request", on_request)

        # Warm up
        print("Warming up session...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(6)

        print(f"Opening contact: {CONTACT_URL}")
        api_calls.clear()
        page.goto(CONTACT_URL, wait_until="domcontentloaded")

        # Wait for content to load
        try:
            page.wait_for_selector('[class*="contact"], [class*="profile"], form, table, .card', timeout=15000)
        except:
            pass
        time.sleep(5)

        # Screenshot
        shot = "/home/user/REI-Blackbook-System-Navigation/screenshots/contact_detail_example.png"
        page.screenshot(path=shot, full_page=True)
        print(f"Screenshot: {shot}")

        # Extract all visible text content
        body_text = page.evaluate("() => document.body.innerText")
        print(f"\nBody length: {len(body_text)} chars")
        print(f"\n=== Page text ===\n{body_text[:3000]}")

        # Show API calls made
        print(f"\n=== API calls ({len(api_calls)}) ===")
        for c in api_calls:
            print(f"  {c['method']} {c['url'][:100]}")

        # Try to call the contact detail API directly
        print("\n=== Direct API probe ===")
        endpoints = [
            f"/profitdial/contacts/{CONTACT_ID}",
            f"/profitdial/contacts/get/{CONTACT_ID}",
            f"/api/contacts/{CONTACT_ID}",
            f"/services/contacts/getContact/{CONTACT_ID}",
        ]
        for ep in endpoints:
            r = page.evaluate(f"""async () => {{
                const r = await fetch('https://my.reiblackbook.com{ep}', {{
                    credentials: 'include',
                    headers: {{'Accept': 'application/json', 'Authorization': 'Bearer', 'X-Requested-With': 'XMLHttpRequest'}}
                }});
                const t = await r.text();
                const isJson = t.trim()[0] === '{{' || t.trim()[0] === '[';
                return {{status: r.status, isJson, preview: t.slice(0, 200)}};
            }}""")
            print(f"  {ep}: {r['status']} json={r['isJson']} | {r['preview'][:80]}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
