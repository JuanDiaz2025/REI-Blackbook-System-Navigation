"""
Post-Visit Auto-Debrief — standalone entrypoint (Mode A).

Polls Google Calendar for property visits that finished since the last run and
runs the pipeline for each. Designed to be invoked on a schedule (cron /
systemd timer / cloud scheduler) or as a simple loop.

  python main.py --once        # process visits from the last POLL_INTERVAL
  python main.py --loop        # poll forever every POLL_INTERVAL_MINUTES

Environment: see .env.example. Keep DRY_RUN=true until the first live write is
approved.
"""

import os
import sys
import time
import json
import datetime

from rei_client import ReiClient, VerificationRequired
from google_clients import GoogleClients
from voicenotes_client import VoicenotesClient
from summarizer import Summarizer
import pipeline

STATE_PATH = os.environ.get("STATE_PATH", "/var/lib/postvisit/state.json")


class Deps:
    """Wires the concrete clients into the shape pipeline.run_visit expects."""
    def __init__(self, google, voicenotes, summarizer_, notify_to):
        self.google = google
        self.voicenotes = voicenotes
        self._summarizer = summarizer_
        self.notify_to = notify_to

    def get_memo(self, address, when):
        return self.voicenotes.get_memo(address, when)

    def find_media(self, address):
        return self.google.find_media(address)

    def summarize(self, transcript):
        return self._summarizer.summarize(transcript)

    def escalate(self, subject, body):
        self.google.send_email(self.notify_to, subject, body)


def _load_state():
    try:
        with open(STATE_PATH) as fh:
            return json.load(fh)
    except Exception:
        return {"processed": []}


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as fh:
        json.dump(state, fh)


def run_once():
    dry_run = os.environ.get("DRY_RUN", "true").lower() != "false"
    interval = int(os.environ.get("POLL_INTERVAL_MINUTES", "30"))

    rei = ReiClient(os.environ["REI_EMAIL"], os.environ["REI_PASSWORD"],
                    cookie_path=os.environ.get("REI_SESSION_PATH", "/tmp/rei_session.pkl"))
    google = GoogleClients()
    deps = Deps(google, VoicenotesClient(), Summarizer(),
                os.environ.get("ESCALATION_TO", ""))

    # REI session — reuse or ask for the verification link (Option C).
    try:
        rei.ensure_session()
    except VerificationRequired as e:
        print("ACTION NEEDED:", e)
        print("Set REI_VERIFY_LINK and re-run, or call rei.complete_verification(link).")
        link = os.environ.get("REI_VERIFY_LINK")
        if not link:
            return
        rei.complete_verification(link)

    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(minutes=interval)
    state = _load_state()
    processed = set(state.get("processed", []))

    visits = google.completed_visits(since, now)
    for v in visits:
        if v.get("event_id") in processed:
            continue
        res = pipeline.run_visit(v, deps, rei, dry_run=dry_run)
        print(json.dumps({
            "address": res["address"], "contact_id": res["contact_id"],
            "classification": res["classification"], "next_step": res["next_step"],
            "written": res["written"], "escalations": res["escalations"],
        }, indent=2))
        processed.add(v.get("event_id"))

    state["processed"] = list(processed)[-500:]
    _save_state(state)


def main():
    if "--loop" in sys.argv:
        interval = int(os.environ.get("POLL_INTERVAL_MINUTES", "30"))
        while True:
            try:
                run_once()
            except Exception as exc:  # keep the loop alive; surface the error
                print("run error:", exc)
            time.sleep(interval * 60)
    else:
        run_once()


if __name__ == "__main__":
    main()
