#!/usr/bin/env python3
"""
Run full navigation of all known REI BlackBook sections with proper CDN rendering.
Loads saved session — no re-login needed.
"""
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import cdn_cache

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"
SCREENSHOTS = Path("/home/user/REI-Blackbook-System-Navigation/screenshots")

KNOWN_SECTIONS = [
    ("Dashboard",                "/"),
    ("Smart_Contacts",           "/contacts"),
    ("Tasks",                    "/services/tasks"),
    ("Deals_List",               "/deals/list"),
    ("Deals_Pipeline",           "/deals/pipeline"),
    ("Property_Pipeline",        "/properties/inbox"),
    ("Multi_Offer_Generator",    "/mog"),
    ("My_Account",               "/services/account/"),
    ("My_Team",                  "/services/users"),
    ("Marketing_Profiles",       "/services/profiles/index"),
    ("System_Settings",          "/profitdial/settings"),
    ("Deal_Settings",            "/contacts/deal-settings"),
]


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

        report = []
        base = "https://my.reiblackbook.com"

        for i, (label, path) in enumerate(KNOWN_SECTIONS):
            url = base + path
            print(f"\n[{i+1:02d}/{len(KNOWN_SECTIONS)}] {label}...")
            try:
                page.goto(url, wait_until="domcontentloaded")
                # Wait for SPA content to mount — try content selectors first, fall back to time
                try:
                    page.wait_for_selector(
                        'table, .card, [class*="contact"], [class*="deal"], [class*="task"], '
                        '[class*="pipeline"], [class*="lead"], [class*="property"], '
                        'form, .panel, .list-group, [class*="grid"], [class*="row"]:not(nav [class*="row"])',
                        timeout=12000,
                    )
                except Exception:
                    time.sleep(10)
                time.sleep(2)
                shot_path = SCREENSHOTS / f"v2_{i+1:02d}_{label}.png"
                page.screenshot(path=str(shot_path), full_page=False)
                entry = {
                    "label": label,
                    "url": page.url,
                    "title": page.title(),
                    "screenshot": str(shot_path),
                    "ok": True,
                }
                print(f"  OK: {page.url}")
            except Exception as e:
                entry = {"label": label, "url": url, "ok": False, "error": str(e)}
                print(f"  ERROR: {e}")
            report.append(entry)

        ctx.close()
        browser.close()

    print("\n=== Summary ===")
    ok = sum(1 for e in report if e.get("ok"))
    print(f"  {ok}/{len(report)} pages captured successfully")
    for e in report:
        status = "OK" if e.get("ok") else "FAIL"
        print(f"  [{status}] {e['label']}: {e.get('url', '')}")

    return report


if __name__ == "__main__":
    main()
