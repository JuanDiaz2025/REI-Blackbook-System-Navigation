"""
REI BlackBook HTTP client.

REI BlackBook has no public API, so this client talks to the same internal
HTTP endpoints the web app uses. It was built by reverse-engineering the
contacts single-page app. All calls reuse one authenticated session (cookie
jar) so we only perform the email-verification login when the session expires.

Endpoints used (discovered from the app bundle):
  GET  /services/account/login/                  login page (session bootstrap)
  POST /services/account/login/                  submit username/password
  GET  /services/account/emailLogin/<token>      follow the emailed verify link
  POST /services/account/emailLogin/<token>      executeLogin=true -> finishes SSO
  GET  /services/account/                         session-alive probe
  GET  /api/contacts/search?q=<name>             search contacts by name
  GET  /contacts/getNotes/<contact_id>           read a contact's notes  (JSON)
  POST /profitdial/contacts/addNote              add a note   (contact_id, body)
  POST /profitdial/contacts/contactDisposition   set disposition / status
  POST /tasks/create                             create a follow-up task

Login requires a per-session email verification link that REI sends to the
account's email. Because that inbox is not machine-readable in this setup,
`login()` raises VerificationRequired; the operator supplies the link and calls
`complete_verification(link)`. Once logged in, the session is persisted and
reused for days, so this is an occasional step, not a per-run one.
"""

import os
import pickle
import requests


REI_BASE = "https://my.reiblackbook.com"

# In the agent sandbox all outbound HTTPS goes through a CA-terminating proxy.
# In a normal deployment neither variable is set and requests talks directly.
_PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
_CA_BUNDLE = "/root/.ccr/ca-bundle.crt" if os.path.exists("/root/.ccr/ca-bundle.crt") else True

_LOGIN_FORM = {
    "remember": "yes",
    "option": "com_users",
    "task": "user.login",
    "return_on_error": "",
    "next": "",
}
_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/141.0 Safari/537.36")


class VerificationRequired(Exception):
    """Raised when REI wants the emailed verification link before logging in."""


class ReiClient:
    def __init__(self, email, password, cookie_path="/tmp/rei_session.pkl"):
        self.email = email
        self.password = password
        self.cookie_path = cookie_path
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": _UA})
        if _PROXY:
            self.s.proxies = {"https": _PROXY, "http": _PROXY}
            self.s.verify = _CA_BUNDLE
        self._pending_verify_url = None
        self._load_cookies()

    # ---- session persistence ------------------------------------------------
    def _load_cookies(self):
        if os.path.exists(self.cookie_path):
            try:
                with open(self.cookie_path, "rb") as fh:
                    self.s.cookies.update(pickle.load(fh))
            except Exception:
                pass

    def _save_cookies(self):
        with open(self.cookie_path, "wb") as fh:
            pickle.dump(self.s.cookies, fh)

    def _xhr(self):
        return {"X-Requested-With": "XMLHttpRequest"}

    # ---- auth ---------------------------------------------------------------
    def is_authenticated(self):
        """True if the persisted session can reach an authed page."""
        r = self.s.get(f"{REI_BASE}/services/account/", allow_redirects=True, timeout=30)
        return "login" not in r.url.lower()

    def login(self):
        """Start a fresh login. Raises VerificationRequired with the pending
        session primed; the operator then supplies the emailed link to
        complete_verification()."""
        self.s.get(f"{REI_BASE}/services/account/login/", timeout=30)
        data = dict(_LOGIN_FORM, username=self.email, password=self.password)
        r = self.s.post(f"{REI_BASE}/services/account/login/", data=data,
                        allow_redirects=True, timeout=45)
        if self.is_authenticated():
            self._save_cookies()
            return True
        if "checkEmail" in r.url or "Verify Your Email" in r.text:
            self._save_cookies()  # keep the pre-verify session
            raise VerificationRequired(
                "REI sent a verification link to the account email. "
                "Call complete_verification(link) with that URL.")
        raise RuntimeError(f"Login failed (landed on {r.url}).")

    def complete_verification(self, link):
        """Finish login using the emailed verification link (same session)."""
        self.s.get(link, allow_redirects=True, timeout=45)
        # The verify page auto-submits a hidden form: POST executeLogin=true.
        self.s.post(link, data={"executeLogin": "true"}, allow_redirects=True, timeout=45)
        if self.is_authenticated():
            self._save_cookies()
            return True
        raise RuntimeError("Verification did not result in an authenticated session.")

    def ensure_session(self):
        """Reuse the session if alive; otherwise trigger login (which may raise
        VerificationRequired)."""
        if self.is_authenticated():
            return True
        return self.login()

    # ---- reads --------------------------------------------------------------
    def search_contacts(self, query):
        """Search contacts by name/email/phone. Returns [{id,name,email}]."""
        r = self.s.get(f"{REI_BASE}/api/contacts/search",
                       params={"q": query}, headers=self._xhr(), timeout=30)
        r.raise_for_status()
        return r.json()

    def get_notes(self, contact_id):
        """Return the contact's notes: {success, notes:[...], total}."""
        r = self.s.get(f"{REI_BASE}/contacts/getNotes/{contact_id}",
                       headers=self._xhr(), timeout=30)
        r.raise_for_status()
        return r.json()

    # ---- writes -------------------------------------------------------------
    def add_note(self, contact_id, body_html):
        """Add a note to a contact. `body_html` may contain simple HTML."""
        r = self.s.post(f"{REI_BASE}/profitdial/contacts/addNote",
                        data={"contact_id": contact_id, "body": body_html},
                        headers=self._xhr(), timeout=45)
        r.raise_for_status()
        return _maybe_json(r)

    def set_disposition(self, contact_id, disposition, **extra):
        """Set the contact's disposition/status. Field names beyond
        contact_id/disposition are account-specific; pass them via **extra
        once confirmed against the account's disposition list."""
        payload = {"contact_id": contact_id, "disposition": disposition}
        payload.update(extra)
        r = self.s.post(f"{REI_BASE}/profitdial/contacts/contactDisposition",
                        data=payload, headers=self._xhr(), timeout=45)
        r.raise_for_status()
        return _maybe_json(r)

    def create_task(self, contact_id, title, due_date, **extra):
        """Create a follow-up task (the 'next step') on a contact.
        due_date: 'YYYY-MM-DD'. Extra task fields vary by account."""
        payload = {"contact_id": contact_id, "title": title, "due_date": due_date}
        payload.update(extra)
        r = self.s.post(f"{REI_BASE}/tasks/create", data=payload,
                        headers=self._xhr(), timeout=45)
        r.raise_for_status()
        return _maybe_json(r)


def _maybe_json(resp):
    try:
        return resp.json()
    except ValueError:
        return {"status_code": resp.status_code, "text": resp.text[:200]}
