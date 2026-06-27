"""
REI Blackbook Navigator
Playwright-based browser automation for the REI Blackbook platform.
Uses direct HTTPS connections (not the system HTTP proxy, which blocks browser CONNECT tunnels).
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import config


class LoginError(Exception):
    pass


class REINavigator:
    def __init__(self, headless: bool = None):
        self.headless = headless if headless is not None else config.HEADLESS
        self.screenshot_dir = Path(config.SCREENSHOT_DIR)
        self.screenshot_dir.mkdir(exist_ok=True)
        self._playwright = None
        self._browser: Browser = None
        self._context: BrowserContext = None
        self.page: Page = None
        self.is_logged_in = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self.headless,
            executable_path="/opt/pw-browsers/chromium",
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                # Use direct connections: the system HTTP proxy blocks Chromium CONNECT tunnels
                # but allows direct outbound HTTPS from the container.
                "--proxy-server=direct://",
                # Allow third-party cookies for the auth.automatedgenius.com SSO flow
                "--disable-features=ThirdPartyCookieBlocking,BlockThirdPartyCookies",
            ],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            ignore_https_errors=True,
        )
        self.page = self._context.new_page()
        self.page.set_default_timeout(config.TIMEOUT)

    def close(self):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def screenshot(self, name: str) -> Path:
        path = self.screenshot_dir / f"{name}.png"
        self.page.screenshot(path=str(path), full_page=True)
        print(f"  [screenshot] {path}")
        return path

    def _check_login_error(self) -> str | None:
        try:
            return self.page.evaluate("""() => {
                const body = document.body.innerText;
                if (body.includes('Username or password was incorrect')) return 'Username or password was incorrect';
                if (body.includes('User account is blocked')) return 'Account blocked';
                if (body.includes('Too many failed login')) return 'Too many failed logins - account locked';
                return null;
            }""")
        except Exception:
            return None

    def login(self, email: str = None, password: str = None) -> bool:
        email = email or config.EMAIL
        password = password or config.PASSWORD

        if not email or not password:
            raise LoginError("EMAIL and PASSWORD must be set (via env vars or config)")

        print(f"Navigating to login page: {config.LOGIN_URL}")
        self.page.goto(config.LOGIN_URL, wait_until="domcontentloaded")
        # Wait for the SSO broker check to complete before interacting
        time.sleep(2)
        self.screenshot("01_login_page")

        # Check if we were auto-logged in via SSO broker session restore
        if "login" not in self.page.url.lower():
            print(f"  Auto-logged in via SSO — URL: {self.page.url}")
            self.is_logged_in = True
            return True

        # Fill and submit the login form
        user_sel = 'input[name="username"]'
        self.page.wait_for_selector(user_sel, timeout=config.TIMEOUT)
        self.page.fill(user_sel, email)
        print(f"  Username: {email}")

        self.page.fill('input[type="password"]', password)
        print("  Password: [provided]")
        self.screenshot("02_login_filled")

        self.page.click('button[type="submit"]')

        # Wait for either a redirect away from login or a networkidle
        try:
            self.page.wait_for_url(
                lambda url: "login" not in url.lower(),
                timeout=config.TIMEOUT,
            )
            self.is_logged_in = True
            print(f"  Login succeeded — URL: {self.page.url}")
            self.screenshot("03_dashboard")
            return True
        except Exception:
            pass

        # Give JS a moment to show any error message
        time.sleep(2)
        self.screenshot("03_post_login")

        error = self._check_login_error()
        if error:
            print(f"  Login failed: {error}")
            print("  Verify credentials: ensure REI_EMAIL/REI_PASSWORD are correct.")
            print("  The username field accepts email addresses on this platform.")
            return False

        # May have redirected somewhere unexpected
        current = self.page.url
        if "login" not in current.lower():
            self.is_logged_in = True
            print(f"  Login succeeded — URL: {current}")
            return True

        print(f"  Login failed — still on login page: {current}")
        return False

    def get_nav_links(self) -> list[dict]:
        try:
            return self.page.evaluate("""() => {
                const seen = new Set();
                const results = [];
                const candidates = document.querySelectorAll(
                    'nav a, .sidebar a, .menu a, [class*="nav"] a, [class*="menu"] a, header a'
                );
                for (const el of candidates) {
                    const href = el.getAttribute('href') || '';
                    const text = (el.textContent || '').trim();
                    if (text && href && !href.startsWith('#') && !seen.has(href)) {
                        seen.add(href);
                        results.push({ text, href });
                    }
                }
                return results;
            }""")
        except Exception as e:
            print(f"  Warning: could not collect nav links: {e}")
            return []

    def get_page_headings(self) -> list[str]:
        try:
            return self.page.evaluate("""() => {
                const els = document.querySelectorAll(
                    'h1, h2, h3, h4, .card-title, .section-title, [class*="title"]'
                );
                return [...new Set(
                    Array.from(els)
                        .map(el => (el.textContent || '').trim())
                        .filter(t => t.length > 0 && t.length < 200)
                )].slice(0, 20);
            }""")
        except Exception:
            return []

    def explore_dashboard(self) -> dict:
        print("\nExploring dashboard...")
        result = {
            "url": self.page.url,
            "title": self.page.title(),
            "nav_links": self.get_nav_links(),
            "headings": self.get_page_headings(),
        }
        self.screenshot("04_dashboard")
        print(f"  Title: {result['title']}")
        print(f"  Nav links: {len(result['nav_links'])}")
        print(f"  Headings: {result['headings'][:5]}")
        return result

    def navigate_to(self, href: str, label: str = "", screenshot_name: str = "") -> bool:
        label = label or href
        print(f"\n  Navigating to: {label}")
        try:
            if href.startswith("http"):
                self.page.goto(href, wait_until="domcontentloaded")
            else:
                base = "/".join(self.page.url.split("/")[:3])
                self.page.goto(base + href, wait_until="domcontentloaded")
            time.sleep(1)
            if screenshot_name:
                self.screenshot(screenshot_name)
            return True
        except Exception as e:
            print(f"  Error navigating to {href}: {e}")
            return False

    def run_full_navigation(self, max_pages: int = 5) -> dict:
        report = {
            "login": False,
            "dashboard": {},
            "pages_visited": [],
            "error": None,
        }

        try:
            report["login"] = self.login()
        except LoginError as e:
            report["error"] = str(e)
            return report

        if not report["login"]:
            report["error"] = "Login failed — check REI_EMAIL and REI_PASSWORD"
            return report

        dashboard = self.explore_dashboard()
        report["dashboard"] = dashboard

        visited = set()
        for i, link in enumerate(dashboard.get("nav_links", [])[:max_pages]):
            href = link["href"]
            text = link["text"]
            if href in visited:
                continue
            visited.add(href)
            safe_name = text[:20].replace(" ", "_").replace("/", "").replace("\\", "")
            ok = self.navigate_to(href, label=text, screenshot_name=f"page_{i+1:02d}_{safe_name}")
            report["pages_visited"].append({"text": text, "href": href, "ok": ok})

        return report
