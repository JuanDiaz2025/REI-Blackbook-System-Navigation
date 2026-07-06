"""
Voicenotes client — fetch Juan's post-visit voice memos.

Uses the Voicenotes API with a personal access token (VOICENOTES_API_TOKEN).
We match a memo to a visit by the property address appearing in the transcript,
preferring the note created closest to the visit time.

NOTE: The Voicenotes REST base/path is set below and should be confirmed against
your account's API docs; the token is a Bearer token in the Authorization header.
"""

import os
import datetime
import requests

VOICENOTES_BASE = os.environ.get("VOICENOTES_BASE", "https://api.voicenotes.com/api")


class VoicenotesClient:
    def __init__(self, token=None):
        self.token = token or os.environ["VOICENOTES_API_TOKEN"]
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        })

    def _recent(self, limit=50):
        r = self.s.get(f"{VOICENOTES_BASE}/recordings",
                       params={"per_page": limit}, timeout=30)
        r.raise_for_status()
        data = r.json()
        # Accept a few common envelope shapes.
        return data.get("data") or data.get("recordings") or data.get("notes") or []

    @staticmethod
    def _transcript(note):
        return (note.get("transcript") or note.get("text")
                or note.get("body") or note.get("title") or "")

    @staticmethod
    def _created(note):
        raw = note.get("created_at") or note.get("date") or ""
        try:
            return datetime.datetime.fromisoformat(str(raw)[:19])
        except Exception:
            return None

    def get_memo(self, address, when=None):
        """Return the transcript of the memo mentioning `address`, closest in
        time to `when`. None if no memo matches."""
        street = address.split(",")[0].strip().lower()
        needle = " ".join(street.split()[:2])  # e.g. "5064 lenelle"
        matches = []
        for note in self._recent():
            t = self._transcript(note)
            if needle and needle in t.lower():
                matches.append(note)
        if not matches:
            return None
        if when:
            try:
                target = datetime.datetime.fromisoformat(str(when)[:19].replace("Z", ""))
                matches.sort(key=lambda n: abs(
                    ((self._created(n) or target) - target).total_seconds()))
            except Exception:
                pass
        return self._transcript(matches[0])
