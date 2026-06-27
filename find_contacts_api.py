#!/usr/bin/env python3
"""
Visit dashboard first (loads SystemJS), then contacts page.
Intercept all network requests to find the real contacts data API.
"""
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

        # Capture responses with bodies for reiblackbook JSON
        json_responses = []
        all_req_urls = []

        async def on_response(response):
            url = response.url
            if "reiblackbook.com" in url:
                all_req_urls.append(url)

        page.on("request", lambda r: all_req_urls.append(r.url) if "reiblackbook.com" in r.url else None)

        # Step 1: Load dashboard first
        print("Step 1: Loading dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(7)
        print(f"  Body length: {page.evaluate('() => document.body.innerText.length')}")

        # Step 2: Navigate to contacts
        print("\nStep 2: Navigating to contacts...")
        all_req_urls.clear()
        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")

        # Wait for table to appear
        try:
            page.wait_for_selector('table tbody tr, [class*="contacts-list"] [class*="row"]', timeout=20000)
            print("  Table found!")
        except:
            print("  Table not found after 20s, waiting more...")
            time.sleep(10)

        time.sleep(3)

        # Check DOM
        dom = page.evaluate("""() => ({
            tableRows: document.querySelectorAll('table tbody tr').length,
            bodyLen: document.body.innerText.length,
            bodyPreview: document.body.innerText.slice(0, 300),
            hasPhone: /\\(\\d{3}\\)/.test(document.body.innerText),
        })""")
        print(f"\nDOM state: {json.dumps(dom, indent=2)}")

        # Show all unique reiblackbook requests
        print(f"\nAll reiblackbook requests ({len(all_req_urls)}):")
        seen = set()
        for u in all_req_urls:
            if u not in seen:
                seen.add(u)
                print(f"  {u[:120]}")

        # Try to get contact data via page's fetch
        print("\n\nProbing API endpoints from page context...")
        endpoints_to_try = [
            "https://my.reiblackbook.com/services/contacts/getContactList",
            "https://my.reiblackbook.com/services/contacts/index/",
            "https://my.reiblackbook.com/contacts/",
            "https://my.reiblackbook.com/index.php?option=com_reibb_contacts&view=contacts&format=json&task=contacts.getContacts",
            "https://my.reiblackbook.com/index.php?option=com_reibb_contacts&view=contacts&format=raw",
        ]

        for url in endpoints_to_try:
            r = page.evaluate(f"""async () => {{
                const r = await fetch("{url}", {{
                    credentials: 'include',
                    headers: {{'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}}
                }});
                const t = await r.text();
                const isJson = t.trim()[0] === '{{' || t.trim()[0] === '[';
                return {{ok: r.ok, status: r.status, json: isJson, preview: t.slice(0, 120)}};
            }}""")
            print(f"  {url.split('.com')[1][:60]}: {r['status']} json={r['json']} | {r['preview'][:60]}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
