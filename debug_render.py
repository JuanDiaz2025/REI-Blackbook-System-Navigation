#!/usr/bin/env python3
"""
Debug script: loads saved session, navigates to dashboard,
captures network requests and checks if CDN assets are loading.
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"
SCREENSHOTS = Path("/home/user/REI-Blackbook-System-Navigation/screenshots")

failed_urls = []
loaded_urls = []

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
                # Force GPU-free software rendering (needed in headless containers)
                "--disable-gpu",
                "--disable-software-rasterizer",
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

        # Track network requests
        def on_response(response):
            url = response.url
            status = response.status
            if "mastercdn" in url or "atm.gs" in url or "reiblackbook" in url:
                if status >= 400:
                    failed_urls.append(f"  FAIL {status}: {url}")
                else:
                    loaded_urls.append(f"  OK   {status}: {url[:100]}")

        def on_request_failed(request):
            url = request.url
            if "mastercdn" in url or "atm.gs" in url or "reiblackbook" in url:
                failed_urls.append(f"  FAIL (network): {url}")

        page.on("response", on_response)
        page.on("requestfailed", on_request_failed)

        # Block only analytics/tracking, NOT CDN or app assets
        BLOCK_PATTERNS = [
            "*google-analytics*",
            "*googletagmanager*",
            "*facebook.net*",
            "*fbcdn*",
            "*hubspot*",
            "*hs-scripts*",
            "*adroll*",
            "*profitwell*",
            "*linkedin.com/li*",
            "*doubleclick.net*",
            "*hotjar*",
        ]
        for pat in BLOCK_PATTERNS:
            ctx.route(pat, lambda route: route.abort())

        print("Navigating to dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")

        # Wait up to 15s for a styled nav element to appear
        print("Waiting for styled elements...")
        try:
            # Try several selectors that would only appear after JS/CSS loads
            for sel in ['.navbar', '.sidebar', 'nav.main-nav', '.main-menu', '#sidebar', '.app-sidebar', '[class*="sidebar"]', '[class*="navbar"]', 'ul.menu', '.nav-menu']:
                try:
                    page.wait_for_selector(sel, timeout=5000)
                    print(f"  Found selector: {sel}")
                    break
                except Exception:
                    pass
        except Exception as e:
            print(f"  No nav selector found: {e}")

        # Extra wait for JS to finish rendering
        time.sleep(5)

        # Check computed styles on key elements
        nav_info = page.evaluate("""() => {
            const results = {};
            const body = document.body;
            if (body) {
                const cs = window.getComputedStyle(body);
                results.bodyBg = cs.backgroundColor;
                results.bodyFont = cs.fontFamily;
            }
            // Find any nav/sidebar
            const selectors = ['nav', '.sidebar', '#sidebar', '.navbar', '[class*="sidebar"]', '[class*="navbar"]'];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    const cs = window.getComputedStyle(el);
                    results[sel] = {
                        bg: cs.backgroundColor,
                        color: cs.color,
                        display: cs.display,
                        position: cs.position,
                        width: cs.width,
                        height: cs.height,
                        className: el.className,
                    };
                    break;
                }
            }
            // Count stylesheets
            results.stylesheets = document.styleSheets.length;
            results.linkedStyles = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
            results.scripts = document.scripts.length;
            results.title = document.title;
            results.url = window.location.href;
            results.bodyHTML_sample = document.body.innerHTML.slice(0, 500);
            return results;
        }""")

        print("\n=== Page Info ===")
        print(json.dumps(nav_info, indent=2))

        print("\n=== Loaded CDN/App URLs (sample) ===")
        for u in loaded_urls[:20]:
            print(u)

        print(f"\n=== Failed URLs ({len(failed_urls)}) ===")
        for u in failed_urls[:20]:
            print(u)

        shot = SCREENSHOTS / "debug_render.png"
        page.screenshot(path=str(shot), full_page=True)
        print(f"\nScreenshot saved: {shot}")

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
