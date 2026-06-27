"""
REI Blackbook Navigator
Playwright-based browser automation for the REI Blackbook platform.
Uses direct HTTPS connections for REI Blackbook domains; CDN assets (mastercdn.atm.gs)
are fetched via curl through the system proxy and served to Playwright via route
interception, working around Chromium's inability to reach the CDN through the proxy.
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
import config
import cdn_cache


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
                # Use direct connections for REI Blackbook domains; CDN assets are
                # served via Playwright route interception (cdn_cache.py) instead.
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
        cdn_cache.install_routes(self._context)
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

    def _is_email_verification_page(self) -> bool:
        return "checkEmail" in self.page.url or "verif" in self.page.url.lower()

    def verify_email_link(self, verification_url: str) -> bool:
        """
        Complete the email-based MFA step by navigating to the verification link
        from the email REI Blackbook sends to the account address after login.

        The page shows "Email Verified Successfully" and contains a hidden form
        (#formLogin) that must be submitted to finalize the session — the JS
        auto-submit does not fire reliably in headless mode, so we trigger it
        explicitly.
        """
        print("  Navigating to email verification link...")
        self.page.goto(verification_url, wait_until="domcontentloaded")
        time.sleep(2)
        self.screenshot("03b_email_verify_page")

        # Submit the hidden #formLogin that finalises the verified session
        submitted = self.page.evaluate("""() => {
            const f = document.querySelector('form#formLogin');
            if (f) { f.submit(); return true; }
            return false;
        }""")

        if submitted:
            print("  Submitted #formLogin to finalise session...")
        else:
            print("  #formLogin not found — waiting for auto-redirect...")

        try:
            self.page.wait_for_url(
                lambda url: "emailLogin" not in url and "checkEmail" not in url and "login" not in url.lower(),
                timeout=config.TIMEOUT,
            )
        except Exception:
            pass

        time.sleep(2)
        self.screenshot("03c_after_email_verify")
        current = self.page.url

        if "emailLogin" not in current and "checkEmail" not in current and "login" not in current.lower():
            self.is_logged_in = True
            print(f"  Email verification succeeded — URL: {current}")
            return True

        print(f"  Email verification may have failed — URL: {current}")
        return False

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
        if "login" not in self.page.url.lower() and not self._is_email_verification_page():
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

        # Wait for redirect away from login page
        try:
            self.page.wait_for_url(
                lambda url: "login" not in url.lower(),
                timeout=config.TIMEOUT,
            )
        except Exception:
            pass

        time.sleep(2)
        self.screenshot("03_post_login")
        current = self.page.url

        # Credentials rejected
        error = self._check_login_error()
        if error:
            print(f"  Login failed: {error}")
            print("  Verify credentials: ensure REI_EMAIL/REI_PASSWORD are correct.")
            return False

        # Still on login page without a known error
        if "login" in current.lower() and not self._is_email_verification_page():
            print(f"  Login failed — still on login page: {current}")
            return False

        # Email MFA verification required
        if self._is_email_verification_page():
            print("  Email verification required.")
            print(f"  REI Blackbook sent a verification link to: {email}")
            print("  Check your inbox for an email from noreply@reiblackbook.com")
            print("  Pass the link to verify_email_link() to continue, or set")
            print("  REI_VERIFY_URL env var and re-run.")
            verify_url = os.environ.get("REI_VERIFY_URL", "")
            if verify_url:
                return self.verify_email_link(verify_url)
            # Mark as needing verification (not a hard failure)
            self.is_logged_in = False
            return False

        self.is_logged_in = True
        print(f"  Login succeeded — URL: {current}")
        self.screenshot("03_dashboard")
        return True

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
            time.sleep(4)
            if screenshot_name:
                self.screenshot(screenshot_name)
            return True
        except Exception as e:
            print(f"  Error navigating to {href}: {e}")
            return False

    def run_full_navigation(self, max_pages: int = 5) -> dict:
        report = {
            "login": False,
            "mfa_required": False,
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
            if self._is_email_verification_page():
                report["mfa_required"] = True
                report["error"] = "Email verification required — check inbox for link from noreply@reiblackbook.com, then set REI_VERIFY_URL"
            else:
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

    # Known navigation sections discovered from a full session exploration
    KNOWN_SECTIONS = [
        ("Dashboard",              "/"),
        ("Smart Contacts",         "/contacts"),
        ("Tasks",                  "/services/tasks"),
        ("Deals",                  "/deals/list"),
        ("Pipelines",              "/deals/pipeline"),
        ("Legacy Property Pipeline", "/properties/inbox"),
        ("Multi Offer Generator",  "/mog"),
        ("My Account",             "/services/account/"),
        ("My Team",                "/services/users"),
        ("Marketing Profiles",     "/services/profiles/index"),
        ("System Settings",        "/profitdial/settings"),
        ("Deal Settings",          "/contacts/deal-settings"),
    ]

    def run_known_sections(self) -> dict:
        """Navigate every known REI Blackbook section and take screenshots."""
        report = {"login": False, "mfa_required": False, "pages": [], "error": None}

        try:
            report["login"] = self.login()
        except LoginError as e:
            report["error"] = str(e)
            return report

        if not report["login"]:
            if self._is_email_verification_page():
                report["mfa_required"] = True
                report["error"] = "Email verification required — check inbox for link from noreply@reiblackbook.com, then set REI_VERIFY_URL"
            else:
                report["error"] = "Login failed — check REI_EMAIL and REI_PASSWORD"
            return report

        base = "https://my.reiblackbook.com"
        for i, (label, path) in enumerate(self.KNOWN_SECTIONS):
            url = base + path
            try:
                self.page.goto(url, wait_until="domcontentloaded")
                time.sleep(5)
                shot = f"{i:02d}_{label.replace(' ', '_').replace('/', '')}"
                self.screenshot(shot)
                entry = {"label": label, "url": self.page.url, "title": self.page.title(), "ok": True}
            except Exception as e:
                entry = {"label": label, "url": url, "ok": False, "error": str(e)}
                print(f"  ERROR on {label}: {e}")
            report["pages"].append(entry)
            print(f"  {label}: {entry['url']}")

        return report
