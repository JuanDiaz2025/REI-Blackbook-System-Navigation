"""
Google clients — Calendar (trigger), Drive (media), Gmail (escalations).

One OAuth credential covers all three. Authorize once (opens a browser and
writes GOOGLE_TOKEN_PATH); subsequent runs refresh silently.

Scopes:
  https://www.googleapis.com/auth/calendar.readonly
  https://www.googleapis.com/auth/drive.readonly
  https://www.googleapis.com/auth/gmail.send
"""

import os
import re
import base64
import datetime
from email.mime.text import MIMEText

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/gmail.send",
]

# Property-visit event titles look like "Property Visit - <address>".
_VISIT_TITLE = re.compile(r"property\s*visit", re.I)
# The REI contact id lives in the event description as a contacts/<id> link.
_REI_CONTACT = re.compile(r"reiblackbook\.com/contacts/(\d+)")


def _credentials():
    token_path = os.environ["GOOGLE_TOKEN_PATH"]
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.environ["GOOGLE_OAUTH_CLIENT_JSON"], SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as fh:
            fh.write(creds.to_json())
    return creds


class GoogleClients:
    def __init__(self):
        creds = _credentials()
        self.calendar = build("calendar", "v3", credentials=creds, cache_discovery=False)
        self.drive = build("drive", "v3", credentials=creds, cache_discovery=False)
        self.gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # ---- Calendar: completed property visits (the trigger) ------------------
    def completed_visits(self, since, until):
        """Return visits whose end time is in [since, until].
        Each: {address, contact_id, seller, end_time}."""
        events = self.calendar.events().list(
            calendarId="primary", timeMin=since.isoformat() + "Z",
            timeMax=until.isoformat() + "Z", singleEvents=True,
            orderBy="startTime", q="property visit").execute().get("items", [])
        out = []
        for e in events:
            title = e.get("summary", "")
            if not _VISIT_TITLE.search(title):
                continue
            end = e.get("end", {}).get("dateTime") or e.get("end", {}).get("date")
            desc = e.get("description", "") or ""
            m = _REI_CONTACT.search(desc)
            address = re.sub(r"(?i)^.*?property\s*visit[\s:–-]*", "", title).strip()
            out.append({
                "address": address or title,
                "contact_id": m.group(1) if m else None,
                "seller": _seller_from_desc(desc),
                "end_time": end,
                "event_id": e.get("id"),
            })
        return out

    # ---- Drive: the property's media folder ---------------------------------
    def find_media(self, address):
        """Find the address-named folder and split video vs. photos."""
        key = _short_address(address)
        q = ("mimeType='application/vnd.google-apps.folder' and trashed=false "
             f"and name contains '{key}'")
        folders = self.drive.files().list(
            q=q, fields="files(id,name)", pageSize=5).execute().get("files", [])
        if not folders:
            return {"photos": [], "video": None, "folder": None}
        folder = folders[0]
        items = self.drive.files().list(
            q=f"'{folder['id']}' in parents and trashed=false",
            fields="files(id,name,mimeType,webViewLink)", pageSize=200
        ).execute().get("files", [])
        photos, video = [], None
        for f in items:
            mt = f.get("mimeType", "")
            if mt.startswith("video/") and not video:
                video = f.get("webViewLink")
            elif mt.startswith("image/"):
                photos.append(f.get("webViewLink"))
        return {"photos": photos, "video": video, "folder": folder["name"]}

    # ---- Gmail: escalation notifications ------------------------------------
    def send_email(self, to, subject, body):
        msg = MIMEText(body)
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        self.gmail.users().messages().send(userId="me", body={"raw": raw}).execute()


def _seller_from_desc(desc):
    m = re.search(r"(?:name|lead)\s*:\s*([A-Za-z][A-Za-z .'-]+)", desc, re.I)
    return m.group(1).strip() if m else ""


def _short_address(address):
    """Street portion only, e.g. '5064 Lenelle Ct, San Jose' -> '5064 Lenelle'."""
    street = address.split(",")[0].strip()
    parts = street.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else street
