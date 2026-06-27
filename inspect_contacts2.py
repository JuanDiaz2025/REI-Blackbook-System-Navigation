#!/usr/bin/env python3
"""Deep inspect: console errors, JS network, wait longer for SPA mount."""
import time, json
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

        console_msgs = []
        failed_reqs = []
        ok_reqs = []

        page.on("console", lambda msg: console_msgs.append(f"[{msg.type}] {msg.text[:200]}"))
        page.on("requestfailed", lambda r: failed_reqs.append(f"{r.failure}: {r.url[:100]}"))
        page.on("response", lambda r: ok_reqs.append(f"{r.status}: {r.url[:80]}") if r.status >= 400 else None)

        print("Loading contacts page with 20s wait...")
        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")
        time.sleep(20)

        print("\n=== Console errors ===")
        errors = [m for m in console_msgs if '[error]' in m or '[warning]' in m]
        for e in errors[:20]:
            print(e)

        print(f"\n=== Failed requests ({len(failed_reqs)}) ===")
        for r in failed_reqs[:15]:
            print(r)

        print(f"\n=== 4xx/5xx responses ({len(ok_reqs)}) ===")
        for r in ok_reqs[:10]:
            print(r)

        # Check what's in the DOM now
        dom_info = page.evaluate("""() => {
            const body = document.body.innerText;
            return {
                tableRows: document.querySelectorAll('table tbody tr').length,
                allLinks: document.querySelectorAll('a').length,
                bodyLength: body.length,
                bodyPreview: body.slice(0, 500),
                // Look for React root
                reactRoot: !!document.querySelector('#root, #app, [data-reactroot]'),
                // SystemJS loaded?
                hasSystem: typeof System !== 'undefined',
                // Any SPA content?
                mainContent: document.querySelector('main, [role="main"], #main, .main-content')?.innerHTML?.slice(0, 500),
            };
        }""")
        print("\n=== DOM after 20s ===")
        print(json.dumps(dom_info, indent=2))

        # Try API directly
        api_result = page.evaluate("""async () => {
            try {
                const r = await fetch('/api/contacts?page=1&limit=5', {credentials: 'include'});
                return { status: r.status, url: r.url, ok: r.ok };
            } catch(e) {
                return { error: e.message };
            }
        }""")
        print("\n=== API test (/api/contacts) ===")
        print(json.dumps(api_result, indent=2))

        # Try the page URL for contacts with different paths
        for path in ['/contacts', '/contacts/list', '/contacts?view=list']:
            result = page.evaluate(f"""async () => {{
                try {{
                    const r = await fetch('{path}', {{credentials: 'include', headers: {{'Accept': 'application/json'}}}});
                    const text = await r.text();
                    return {{ status: r.status, preview: text.slice(0, 200) }};
                }} catch(e) {{ return {{ error: e.message }}; }}
            }}""")
            print(f"\nFetch {path}: {json.dumps(result)}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
