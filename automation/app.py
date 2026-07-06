"""
Post-Visit Auto-Debrief — desktop app (local dashboard).

Runs a small local web server and opens the dashboard in your browser, so it
behaves like a desktop app on Windows. It reuses the automation backend
(rei_client / pipeline / google / voicenotes / summarizer).

Start with:  run.bat   (Windows)   or   python app.py

Config (API keys, REI login) is saved locally to config.json next to this file
and is never uploaded anywhere.
"""

import os
import sys
import json
import threading
import webbrowser
import traceback

from flask import Flask, request, jsonify, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")
UI_DIR = os.path.join(HERE, "ui")

app = Flask(__name__, static_folder=None)

# ---- config (saved locally) -------------------------------------------------
DEFAULT_CONFIG = {
    "REI_EMAIL": "", "REI_PASSWORD": "",
    "GOOGLE_OAUTH_CLIENT_JSON": "", "GOOGLE_TOKEN_PATH": os.path.join(HERE, "google_token.json"),
    "VOICENOTES_API_TOKEN": "", "ANTHROPIC_API_KEY": "",
    "ANTHROPIC_MODEL": "claude-opus-4-8",
    "ESCALATION_TO": "", "POLL_INTERVAL_MINUTES": "1440", "DRY_RUN": "true",
    "REI_SESSION_PATH": os.path.join(HERE, "rei_session.pkl"),
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            cfg.update(json.load(open(CONFIG_PATH)))
        except Exception:
            pass
    return cfg


def save_config(cfg):
    json.dump(cfg, open(CONFIG_PATH, "w"), indent=2)


def apply_env(cfg):
    for k, v in cfg.items():
        if v not in (None, ""):
            os.environ[k] = str(v)


# ---- UI ---------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        cfg = load_config()
        cfg.update(request.get_json(force=True) or {})
        save_config(cfg)
        return jsonify({"ok": True})
    cfg = load_config()
    # never send secrets back to the browser in full — just whether they're set
    masked = {k: (bool(v) if any(s in k for s in ("PASSWORD", "TOKEN", "KEY")) else v)
              for k, v in cfg.items()}
    return jsonify(masked)


# ---- REI session ------------------------------------------------------------
@app.route("/api/rei/status")
def rei_status():
    cfg = load_config(); apply_env(cfg)
    try:
        from rei_client import ReiClient
        rei = ReiClient(cfg["REI_EMAIL"], cfg["REI_PASSWORD"], cfg["REI_SESSION_PATH"])
        return jsonify({"authenticated": rei.is_authenticated()})
    except Exception as e:
        return jsonify({"authenticated": False, "error": str(e)})


@app.route("/api/rei/login", methods=["POST"])
def rei_login():
    """Kick off login; report whether a verification link is needed."""
    cfg = load_config(); apply_env(cfg)
    from rei_client import ReiClient, VerificationRequired
    rei = ReiClient(cfg["REI_EMAIL"], cfg["REI_PASSWORD"], cfg["REI_SESSION_PATH"])
    try:
        if rei.is_authenticated():
            return jsonify({"status": "authenticated"})
        rei.login()
        return jsonify({"status": "authenticated"})
    except VerificationRequired:
        return jsonify({"status": "verification_needed"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/rei/verify", methods=["POST"])
def rei_verify():
    cfg = load_config(); apply_env(cfg)
    link = (request.get_json(force=True) or {}).get("link", "").strip()
    from rei_client import ReiClient
    rei = ReiClient(cfg["REI_EMAIL"], cfg["REI_PASSWORD"], cfg["REI_SESSION_PATH"])
    try:
        rei.complete_verification(link)
        return jsonify({"status": "authenticated"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# ---- run the pipeline -------------------------------------------------------
@app.route("/api/run", methods=["POST"])
def api_run():
    cfg = load_config(); apply_env(cfg)
    opts = request.get_json(force=True) or {}
    dry_run = opts.get("dry_run", cfg.get("DRY_RUN", "true") != "false")
    hours = int(opts.get("hours", 24))
    try:
        results = _run_pipeline(cfg, hours=hours, dry_run=dry_run)
        return jsonify({"ok": True, "results": results, "dry_run": dry_run})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()[-800:]})


def _run_pipeline(cfg, hours, dry_run):
    import datetime
    from rei_client import ReiClient
    from google_clients import GoogleClients
    from voicenotes_client import VoicenotesClient
    from summarizer import Summarizer
    import pipeline

    rei = ReiClient(cfg["REI_EMAIL"], cfg["REI_PASSWORD"], cfg["REI_SESSION_PATH"])
    google = GoogleClients()
    voicenotes = VoicenotesClient()
    summarizer = Summarizer()

    class Deps:
        def get_memo(self, address, when): return voicenotes.get_memo(address, when)
        def find_media(self, address): return google.find_media(address)
        def summarize(self, transcript): return summarizer.summarize(transcript)
        def escalate(self, subject, body): google.send_email(cfg.get("ESCALATION_TO", ""), subject, body)

    now = datetime.datetime.utcnow()
    since = now - datetime.timedelta(hours=hours)
    out = []
    for v in google.completed_visits(since, now):
        res = pipeline.run_visit(v, Deps(), rei, dry_run=dry_run)
        out.append({
            "address": res["address"], "seller": v.get("seller", ""),
            "classification": res["classification"], "next_step": res["next_step"],
            "follow_up_date": res["follow_up_date"], "score": res["score"],
            "note_html": res["note_html"], "escalations": res["escalations"],
            "written": res["written"], "contact_id": res["contact_id"],
        })
    return out


def _open_browser():
    webbrowser.open("http://127.0.0.1:5000/")


if __name__ == "__main__":
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    if "--no-browser" not in sys.argv:
        threading.Timer(1.2, _open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
