#!/usr/bin/env python3
"""Inspect the contacts page DOM to find correct selectors."""
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

        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")
        time.sleep(8)  # extra wait for React to mount

        info = page.evaluate("""() => {
            const results = {};

            // Count common structural elements
            results.tables = document.querySelectorAll('table').length;
            results.tableRows = document.querySelectorAll('table tbody tr').length;
            results.allRows = document.querySelectorAll('tr').length;

            // Body text snippet for pagination
            const body = document.body.innerText;
            const showMatch = body.match(/Showing[^\\n]{0,60}/i);
            results.showingText = showMatch ? showMatch[0] : null;

            // Find elements with "contact" in class
            const contactEls = document.querySelectorAll('[class*="contact"]');
            results.contactClassCount = contactEls.length;
            if (contactEls.length > 0) {
                results.contactClassSamples = Array.from(contactEls).slice(0,5).map(e => ({
                    tag: e.tagName,
                    cls: e.className.slice(0,80),
                    text: e.textContent.trim().slice(0,60),
                }));
            }

            // Find all links with /contacts/ in href
            const contactLinks = document.querySelectorAll('a[href*="/contacts/"]');
            results.contactLinks = Array.from(contactLinks).slice(0,5).map(a => ({
                href: a.getAttribute('href'),
                text: a.textContent.trim().slice(0,40),
            }));

            // Pagination info
            const paginationEls = document.querySelectorAll('[class*="pagination"], [class*="pager"]');
            results.paginationCount = paginationEls.length;
            if (paginationEls.length > 0) {
                results.paginationHTML = paginationEls[0].innerHTML.slice(0,300);
            }

            // Any data-* attributes that look like contact IDs
            const dataEls = document.querySelectorAll('[data-id], [data-contact-id], [data-row]');
            results.dataEls = dataEls.length;

            // Inner text search for phone patterns
            const phoneMatch = body.match(/\\(\\d{3}\\)\\s*\\d{3}[\\s\\-]\\d{4}/);
            results.phoneFound = phoneMatch ? phoneMatch[0] : null;

            // Sample of visible text structure
            results.bodyPreview = body.slice(0, 800);

            return results;
        }""")

        print(json.dumps(info, indent=2))

        # Also dump a chunk of the HTML to see the structure
        html_sample = page.evaluate("""() => {
            // Find the main content area
            const main = document.querySelector('main, #app, [class*="content"], [class*="main"]');
            return main ? main.innerHTML.slice(0, 3000) : document.body.innerHTML.slice(0, 3000);
        }""")
        print("\n=== HTML SAMPLE ===")
        print(html_sample[:3000])

        ctx.close()
        browser.close()

if __name__ == "__main__":
    main()
