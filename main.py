#!/usr/bin/env python3
"""
REI Blackbook System Navigator
Logs in and explores the REI Blackbook platform via Playwright.

Usage:
    REI_EMAIL=you@example.com REI_PASSWORD=secret python3 main.py

Or copy .env.example to .env and fill in your credentials.
"""
import json
import sys
from rei_navigator import REINavigator


def main():
    print("=== REI Blackbook System Navigator ===\n")

    with REINavigator(headless=True) as nav:
        report = nav.run_full_navigation()

    print("\n=== Navigation Report ===")
    print(json.dumps(report, indent=2))

    if report.get("error"):
        print(f"\nError: {report['error']}")
        sys.exit(1)

    if not report["login"]:
        print("\nLogin failed. Check credentials in .env or environment variables.")
        sys.exit(1)

    pages = report.get("pages_visited", [])
    ok_count = sum(1 for p in pages if p.get("ok"))
    print(f"\nVisited {ok_count}/{len(pages)} pages successfully.")
    print(f"Screenshots saved to: {nav.screenshot_dir}/")


if __name__ == "__main__":
    main()
