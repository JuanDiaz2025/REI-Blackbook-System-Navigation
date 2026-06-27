#!/usr/bin/env python3
"""
Scrape ALL contacts from REI BlackBook via the profitdial/contacts/query API.
Uses a single POST request to retrieve all 7,720 contacts at once.
Saves full data as JSON and a cleaned CSV.
"""
import csv
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import cdn_cache

SESSION_FILE = "/tmp/claude-0/-home-user-REI-Blackbook-System-Navigation/653e0dd0-1f91-569f-a75b-0535c099b183/scratchpad/rei_session.json"
OUTPUT_DIR = Path("/home/user/REI-Blackbook-System-Navigation")

# Full payload matching what the SPA sends, but without limit/offset so we get all contacts
QUERY_PAYLOAD = {
    "order": "c.id DESC",
    "filters": [],
    "advanced_filter_link": "AND",
    "compound_filter_link": "AND",
    "compound": True,
    "view_columns": [
        "name", "optinEmailStatus", "phone1", "phone2",
        "email", "address", "city", "state", "zip_code",
        "tags", "source", "created_at", "last_activity_at",
    ],
    "query_instance": "contactsTableStore",
    "defaults": ["show_hidden_contacts__boolean__0"],
}


def fetch_all_contacts(page) -> list[dict]:
    """Call the API and return all contacts as a list of dicts."""
    result = page.evaluate(f"""async () => {{
        const r = await fetch('https://my.reiblackbook.com/profitdial/contacts/query', {{
            method: 'POST',
            credentials: 'include',
            headers: {{
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': 'Bearer',
                'X-Requested-With': 'XMLHttpRequest',
            }},
            body: JSON.stringify({json.dumps(QUERY_PAYLOAD)}),
        }});
        if (!r.ok) return {{error: r.status + ' ' + r.statusText}};
        return await r.json();
    }}""")
    return result


def flatten_contact(c: dict) -> dict:
    """Flatten a contact dict to a clean CSV row."""
    tags = c.get("tags", [])
    if isinstance(tags, list):
        tag_str = "; ".join(t.get("name", str(t)) if isinstance(t, dict) else str(t) for t in tags)
    else:
        tag_str = str(tags)

    name_parts = [c.get("honorific",""), c.get("first_name",""), c.get("middle_initial",""), c.get("last_name","")]
    full_name = " ".join(p for p in name_parts if p).strip()

    return {
        "id":              c.get("id",""),
        "full_name":       full_name,
        "first_name":      c.get("first_name",""),
        "last_name":       c.get("last_name",""),
        "email":           c.get("email",""),
        "phone1":          c.get("phone1",""),
        "phone2":          c.get("phone2",""),
        "address":         c.get("address",""),
        "city":            c.get("city",""),
        "state":           c.get("state",""),
        "zip_code":        c.get("zip_code",""),
        "optin_status":    c.get("optinEmailStatus",""),
        "tags":            tag_str,
        "source":          c.get("source",""),
        "created_at":      c.get("created_at",""),
        "last_activity_at":c.get("last_activity_at",""),
    }


def main():
    print("=== REI BlackBook Contact Scraper ===\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path="/opt/pw-browsers/chromium",
            args=[
                "--no-sandbox", "--disable-dev-shm-usage",
                "--proxy-server=direct://",
                "--disable-features=ThirdPartyCookieBlocking,BlockThirdPartyCookies",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            storage_state=SESSION_FILE,
            ignore_https_errors=True,
        )
        cdn_cache.install_routes(ctx)
        page = ctx.new_page()
        page.set_default_timeout(120000)

        # Warm up session (establishes auth context for the API)
        print("Warming up session...")
        page.goto("https://my.reiblackbook.com/", wait_until="domcontentloaded")
        time.sleep(5)

        print("Fetching all contacts via API...")
        t0 = time.time()
        data = fetch_all_contacts(page)
        elapsed = time.time() - t0

        if "error" in data:
            print(f"ERROR: {data['error']}")
            return

        contacts_raw = data.get("contacts", [])
        total_reported = data.get("count", len(contacts_raw))
        print(f"API returned {len(contacts_raw)} contacts (reported total: {total_reported}) in {elapsed:.1f}s")

        ctx.close()
        browser.close()

    # Save raw JSON
    json_path = OUTPUT_DIR / "contacts_all.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(contacts_raw, f, indent=2, ensure_ascii=False)
    print(f"\nRaw JSON saved: {json_path} ({json_path.stat().st_size // 1024}KB)")

    # Flatten and save CSV
    csv_path = OUTPUT_DIR / "contacts_all.csv"
    rows = [flatten_contact(c) for c in contacts_raw]
    if rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV saved:      {csv_path} ({csv_path.stat().st_size // 1024}KB)")

    # Stats
    print(f"\n=== Summary ===")
    print(f"  Total contacts: {len(rows)}")
    emails = [r["email"] for r in rows if r["email"]]
    phones = [r["phone1"] for r in rows if r["phone1"]]
    states = {}
    for r in rows:
        s = (r["state"] or "").strip()
        if s:
            states[s] = states.get(s, 0) + 1
    print(f"  With email:     {len(emails)}")
    print(f"  With phone:     {len(phones)}")
    top_states = sorted(states.items(), key=lambda x: -x[1])[:8]
    print(f"  Top states:     {', '.join(f'{s}({n})' for s,n in top_states)}")

    print("\nSample (first 5):")
    for r in rows[:5]:
        print(f"  [{r['id']}] {r['full_name']} | {r['phone1']} | {r['email']} | {r['tags'][:40]}")

    return rows


if __name__ == "__main__":
    contacts = main()
