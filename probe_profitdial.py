#!/usr/bin/env python3
"""Probe profitdial/contacts/query to understand the API format."""
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

        # Capture the actual profitdial/contacts/query request payload
        captured_requests = []
        def capture(request):
            if 'profitdial/contacts/query' in request.url:
                try:
                    body = request.post_data or ''
                    captured_requests.append({'url': request.url, 'method': request.method, 'body': body[:500], 'headers': dict(request.headers)})
                except:
                    captured_requests.append({'url': request.url, 'method': request.method})

        page.on("request", capture)

        # Load dashboard first
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(6)

        # Navigate to contacts to trigger the API call
        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")
        try:
            page.wait_for_selector('table tbody tr', timeout=20000)
        except:
            time.sleep(10)
        time.sleep(2)

        print(f"=== Captured {len(captured_requests)} profitdial/contacts/query requests ===")
        for r in captured_requests:
            print(json.dumps(r, indent=2))

        # Now try to call it directly
        print("\n=== Direct API calls ===")
        payloads = [
            {"page": 1, "limit": 25},
            {"page": 1, "pageSize": 25},
            {"page": 0, "limit": 25},
            {},
        ]
        for payload in payloads:
            result = page.evaluate(f"""async () => {{
                const r = await fetch('https://my.reiblackbook.com/profitdial/contacts/query', {{
                    method: 'POST',
                    credentials: 'include',
                    headers: {{'Content-Type': 'application/json', 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}},
                    body: JSON.stringify({json.dumps(payload)}),
                }});
                const t = await r.text();
                const isJson = t.trim()[0] === '{{' || t.trim()[0] === '[';
                return {{status: r.status, isJson, len: t.length, preview: t.slice(0, 300)}};
            }}""")
            print(f"\nPayload {payload}: status={result['status']} json={result['isJson']} len={result['len']}")
            if result['isJson']:
                print(f"  Preview: {result['preview']}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
