#!/usr/bin/env python3
"""
Intercept all XHR/fetch requests made by the contacts SPA to find the data API.
Also check reibb.json import map to understand module loading.
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

        all_requests = []
        json_responses = []

        def capture_response(response):
            url = response.url
            ct = response.headers.get("content-type", "")
            # Capture all reiblackbook requests AND json responses
            if "reiblackbook.com" in url or "json" in ct:
                all_requests.append({"url": url[:120], "status": response.status, "ct": ct[:50]})

        def capture_request(request):
            url = request.url
            if "reiblackbook.com" in url and url != "https://my.reiblackbook.com/":
                if any(x in url for x in ['/api/', '/services/', 'contact', 'task', 'deal']):
                    print(f"  REQ: {request.method} {url[:100]}")

        page.on("response", capture_response)
        page.on("request", capture_request)

        # First check the reibb.json import map
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(2)

        reibb = page.evaluate("""async () => {
            try {
                const r = await fetch('https://mastercdn.atm.gs/reibb.json', {credentials: 'omit'});
                return await r.json();
            } catch(e) { return {error: e.message}; }
        }""")
        print("=== reibb.json (import map) ===")
        if 'imports' in reibb:
            for k, v in list(reibb['imports'].items())[:10]:
                print(f"  {k}: {v[:80]}")
        else:
            print(json.dumps(reibb, indent=2)[:500])

        # Now navigate to contacts and capture requests
        print("\n\nNavigating to contacts...")
        all_requests.clear()
        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")
        time.sleep(15)

        print(f"\n=== All reiblackbook.com requests ({len(all_requests)}) ===")
        for r in all_requests:
            if r['status'] != 200 or 'json' in r['ct'] or 'contacts' in r['url']:
                print(f"  [{r['status']}] {r['url']}")
                if r['ct']:
                    print(f"    content-type: {r['ct']}")

        # Try to find the contacts API by intercepting fetch
        contacts_data = page.evaluate("""async () => {
            // Try common API patterns for contacts
            const endpoints = [
                '/index.php?option=com_reibb_contacts&task=contacts.getContacts&format=json',
                '/index.php?option=com_reibb_contacts&format=json',
                '/services/contacts/list',
                '/services/contacts/getAll',
                '/contacts/getContacts',
            ];
            const results = {};
            for (const ep of endpoints) {
                try {
                    const r = await fetch(ep, {
                        credentials: 'include',
                        headers: {'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'}
                    });
                    const text = await r.text();
                    const isJson = text.trim().startsWith('{') || text.trim().startsWith('[');
                    results[ep] = {status: r.status, isJson, preview: text.slice(0, 100)};
                } catch(e) {
                    results[ep] = {error: e.message};
                }
            }
            return results;
        }""")

        print("\n=== Endpoint probes ===")
        for ep, res in contacts_data.items():
            print(f"  {ep}: {json.dumps(res)[:120]}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
