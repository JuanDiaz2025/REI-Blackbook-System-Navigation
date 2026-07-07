#!/usr/bin/env python3
"""Step 5: Download today's call recordings and transcribe them locally.

REI BlackBook stores call recordings (mp3) but NO transcripts, so the only
record of what was actually said is the audio. This transcribes each of today's
recordings from gathered.json using faster-whisper (offline, CPU).

Why this step is mandatory: call metadata (no_answer / left_voicemail flags) is
unreliable. We have seen a call flagged "answered" that the audio proved was a
voicemail. Always classify Contact Result from the transcript, not the flags.

Setup:  pip install faster-whisper   (and have the CA bundle trusted for S3)
Usage:  python3 scripts/05_transcribe.py
        TARGET_DAY=2026-07-07 WMODEL=small.en python3 scripts/05_transcribe.py

Output: ./transcripts.json  { contactId: {name, calls:[{time,direction,duration,text}]} }
"""
import os
import json
import datetime
import urllib.request

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

TARGET_DAY = os.environ.get("TARGET_DAY") or datetime.date.today().isoformat()
WMODEL = os.environ.get("WMODEL", "small.en")  # base.en = faster, small.en = more accurate
CA = os.environ.get("NODE_EXTRA_CA_CERTS")  # proxy CA bundle, if behind the sandbox proxy

REC_DIR = "rec"
os.makedirs(REC_DIR, exist_ok=True)


def fetch(url, dest):
    ctx = None
    if CA:
        import ssl
        ctx = ssl.create_default_context(cafile=CA)
    with urllib.request.urlopen(url, context=ctx, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def main():
    gathered = json.load(open("gathered.json"))
    from faster_whisper import WhisperModel
    model = WhisperModel(WMODEL, device="cpu", compute_type="int8")

    out = {}
    for cid, obj in gathered.items():
        hist = obj["history"]
        c = hist.get("contact", {}) or {}
        name = f"{c.get('first_name','')} {c.get('last_name','')}".strip() or "(unassigned)"
        calls = []
        for call in hist.get("calls", []):
            if not str(call.get("created_at", "")).startswith(TARGET_DAY):
                continue
            link = (call.get("recording") or {}).get("link")
            text = ""
            if link:
                dest = os.path.join(REC_DIR, f"{cid}_{call['id']}.mp3")
                try:
                    fetch(link, dest)
                    segs, info = model.transcribe(dest, beam_size=5, vad_filter=True)
                    text = " ".join(s.text.strip() for s in segs)
                except Exception as e:  # noqa
                    text = f"(transcription failed: {e})"
            calls.append({
                "time": call.get("created_at"),
                "direction": call.get("direction"),
                "duration": call.get("duration"),
                "recording": link,
                "text": text,
            })
        out[cid] = {"name": name, "calls": calls}
        for call in calls:
            print(f"\n=== {cid} {name} | {call['time']} | {call['direction']} | {call['duration']}s ===")
            print(call["text"] or "(no recording)")

    json.dump(out, open("transcripts.json", "w"), indent=1)
    print("\nSaved transcripts.json. Review, then draft notes and run 06_add_note.js.")


if __name__ == "__main__":
    main()
