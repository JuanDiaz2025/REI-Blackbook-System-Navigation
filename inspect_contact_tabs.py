#!/usr/bin/env python3
"""
Click through every tab on a contact detail page and capture all data.
Tabs: About · Chat · Activities · Notes · Tasks · Files · Workflows · Properties
"""
import json, time
from pathlib import Path
from playwright.sync_api import sync_playwright
import cdn_cache

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"
SCREENSHOTS = Path("/home/user/REI-Blackbook-System-Navigation/screenshots/contact_tabs")
SCREENSHOTS.mkdir(exist_ok=True)

CONTACT_ID = "20466744"
CONTACT_URL = f"https://my.reiblackbook.com/contacts/{CONTACT_ID}"

# The tabs as they appear in the UI
CONTACT_TABS = ["About", "Chat", "Activities", "Notes", "Tasks", "Files", "Workflows", "Properties"]


def wait_for_spa(page, timeout=20000):
    """Wait until the contact SPA has mounted (body has more than just nav)."""
    start = time.time()
    while time.time() - start < timeout / 1000:
        length = page.evaluate("() => document.body.innerText.length")
        if length > 500:
            return True
        time.sleep(0.5)
    return False


def get_dom_snapshot(page) -> dict:
    """Capture a full DOM snapshot to understand the tab structure."""
    return page.evaluate("""() => {
        const bodyText = document.body.innerText;

        // Find all elements between y=60 and y=200 (contact tab strip area)
        const allEls = Array.from(document.querySelectorAll('*'));
        const tabArea = allEls.filter(el => {
            const r = el.getBoundingClientRect();
            return r.top > 55 && r.top < 200 && r.width > 10 && r.height > 5 && r.height < 60;
        }).map(el => ({
            tag: el.tagName,
            text: el.innerText?.trim().slice(0, 30),
            cls: el.className?.slice?.(0, 60) || '',
            top: Math.round(el.getBoundingClientRect().top),
            left: Math.round(el.getBoundingClientRect().left),
        })).filter(e => e.text && e.text.length > 1);

        // All clickable elements with tab-like text
        const tabTexts = ['About', 'Chat', 'Activities', 'Notes', 'Tasks', 'Files', 'Workflows', 'Properties'];
        const tabEls = [];
        for (const text of tabTexts) {
            const found = Array.from(document.querySelectorAll('*')).find(el =>
                el.innerText?.trim() === text && el.getBoundingClientRect().width > 0
            );
            if (found) {
                const r = found.getBoundingClientRect();
                tabEls.push({
                    text, tag: found.tagName,
                    cls: found.className?.slice?.(0, 80) || '',
                    top: Math.round(r.top), left: Math.round(r.left),
                    id: found.id,
                });
            }
        }

        return {
            bodyLen: bodyText.length,
            bodyPreview: bodyText.slice(0, 400),
            tabAreaElements: tabArea.slice(0, 30),
            knownTabEls: tabEls,
        };
    }""")


def click_tab(page, tab_text: str) -> bool:
    """Click a contact detail tab by its exact text."""
    result = page.evaluate(f"""() => {{
        const tabTexts = ['{tab_text}'];
        const all = Array.from(document.querySelectorAll('*'));
        // Find the element with exact text that is visible and in the tab area
        for (const el of all) {{
            const t = el.innerText?.trim();
            if (t !== '{tab_text}') continue;
            const r = el.getBoundingClientRect();
            if (r.width > 0 && r.height > 0 && r.top < 400) {{
                el.click();
                return {{found: true, tag: el.tagName, cls: el.className?.slice?.(0,60), top: r.top, left: r.left}};
            }}
        }}
        return {{found: false}};
    }}""")
    if result.get("found"):
        print(f"    Clicked [{result['tag']}] top={result['top']:.0f} cls={result['cls']}")
        return True
    return False


def extract_full_content(page, tab_name: str) -> dict:
    """Extract everything visible in the current tab."""
    return page.evaluate(f"""() => {{
        const body = document.body.innerText;

        // Find the active tab panel
        const panels = document.querySelectorAll(
            '[class*="tab-pane"], [class*="panel"], [class*="tab-content"], [class*="view"], section'
        );
        let panelText = '';
        for (const p of panels) {{
            const r = p.getBoundingClientRect();
            if (r.top > 50 && r.height > 100) {{
                panelText = p.innerText.trim();
                if (panelText.length > 100) break;
            }}
        }}

        // Activity/timeline items
        const items = Array.from(document.querySelectorAll(
            '[class*="activity"], [class*="timeline"], [class*="event"], [class*="feed"], ' +
            '[class*="log"], [class*="history"], [class*="chat"], [class*="message"], ' +
            '[class*="note"], [class*="file"], [class*="workflow"], [class*="task"]'
        )).filter(el => {{
            const r = el.getBoundingClientRect();
            return r.top > 100 && r.width > 100;
        }}).slice(0, 50).map(el => ({{
            cls: el.className?.slice?.(0,40),
            text: el.innerText.trim().slice(0, 300),
        }})).filter(i => i.text.length > 5);

        // Tables
        const tables = Array.from(document.querySelectorAll('table')).map(t => ({{
            headers: Array.from(t.querySelectorAll('th')).map(th => th.innerText.trim()),
            rows: Array.from(t.querySelectorAll('tbody tr')).slice(0,20).map(tr =>
                Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
            ).filter(r => r.some(c => c)),
        }})).filter(t => t.rows.length > 0);

        return {{
            tab: "{tab_name}",
            bodyText: body.slice(0, 4000),
            panelText: panelText.slice(0, 2000),
            items,
            tables,
        }};
    }}""")


def main():
    all_data = {}

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
        page.set_default_timeout(30000)

        # Warm up on dashboard
        print("Warming up session on dashboard...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(7)
        body_len = page.evaluate("() => document.body.innerText.length")
        print(f"  Dashboard body: {body_len} chars")

        # Navigate to contacts list first (loads the contacts SPA module)
        print("Loading contacts list to warm up SPA module...")
        page.goto("https://my.reiblackbook.com/contacts", wait_until="domcontentloaded")
        wait_for_spa(page, 15000)
        body_len = page.evaluate("() => document.body.innerText.length")
        print(f"  Contacts list body: {body_len} chars")
        time.sleep(3)

        # Now open the contact detail
        print(f"\nOpening contact detail: {CONTACT_URL}")
        page.goto(CONTACT_URL, wait_until="domcontentloaded")
        wait_for_spa(page, 20000)
        time.sleep(4)

        # DOM snapshot to understand structure
        snap = get_dom_snapshot(page)
        print(f"\nBody: {snap['bodyLen']} chars")
        print(f"Preview: {snap['bodyPreview'][:200].replace(chr(10), ' | ')}")
        print(f"\nKnown tab elements found: {len(snap['knownTabEls'])}")
        for t in snap["knownTabEls"]:
            print(f"  '{t['text']}' [{t['tag']}] top={t['top']} left={t['left']} cls={t['cls'][:50]}")
        print(f"\nTab-area DOM elements ({len(snap['tabAreaElements'])}):")
        for e in snap["tabAreaElements"][:20]:
            print(f"  [{e['tag']}] top={e['top']} left={e['left']} '{e['text']}' | {e['cls'][:40]}")

        # Screenshot initial state
        page.screenshot(path=str(SCREENSHOTS / "01_About.png"), full_page=True)
        all_data["About"] = extract_full_content(page, "About")
        print(f"\n[About] {len(all_data['About']['bodyText'])} chars")

        # Click each tab
        for i, tab_name in enumerate(CONTACT_TABS[1:], start=2):
            print(f"\n--- Tab: {tab_name} ---")
            clicked = click_tab(page, tab_name)
            if not clicked:
                print(f"  NOT FOUND in DOM")
                # Try clicking ">" overflow button if tab might be hidden
                page.evaluate("""() => {
                    const overflow = document.querySelector('[class*="overflow"], [class*="more"], [class*="chevron"]');
                    if (overflow) overflow.click();
                }""")
                time.sleep(1)
                clicked = click_tab(page, tab_name)
                if not clicked:
                    all_data[tab_name] = {"error": "tab not found in DOM"}
                    continue

            time.sleep(4)
            shot = SCREENSHOTS / f"{i:02d}_{tab_name}.png"
            page.screenshot(path=str(shot), full_page=True)
            data = extract_full_content(page, tab_name)
            all_data[tab_name] = data

            body = data["bodyText"]
            print(f"  Body: {len(body)} chars")
            if data["items"]:
                print(f"  Items: {len(data['items'])}")
                for item in data["items"][:5]:
                    print(f"    [{item['cls'][:25]}] {item['text'][:100].replace(chr(10),' ')}")
            if data["tables"]:
                for tbl in data["tables"]:
                    print(f"  Table ({len(tbl['rows'])} rows): headers={tbl['headers'][:5]}")

        ctx.close()
        browser.close()

    out = "/home/user/REI-Blackbook-System-Navigation/contact_tabs_data.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
