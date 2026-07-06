"""
Post-Visit Auto-Debrief pipeline.

Implements the Equity Track "Post-Property Visit Conversion Process": for a
completed property visit, turn Juan's voice memo into a structured debrief,
locate the Drive media, score the documentation, and update REI BlackBook
(note + next step), escalating any gaps.

The data-gathering steps (calendar, voicenotes, drive) and the LLM
summarization are injected as callables so this module stays provider-agnostic
and testable:

    run_visit(visit, deps, rei, dry_run=True)

`visit`  : {"address","contact_id","seller","end_time"}   (from Calendar)
`deps`   : object exposing
             .get_memo(address, when)   -> transcript str or None
             .find_media(address)       -> {"photos":[...], "video":url|None}
             .summarize(transcript)     -> debrief dict (see SELLER_CLASSES)
             .escalate(subject, body)   -> None  (email/notify)
`rei`    : an authenticated ReiClient
`dry_run`: when True (default) REI writes are previewed, not sent.
"""

import datetime

# Blueprint §9 — classification -> REI follow-up path (the "next step").
SELLER_CLASSES = {
    "Ready Now":          "Same-day offer / contract push",
    "Wants More Money":   "Price-objection sequence + market update",
    "Family Decision":    "Family-decision follow-up sequence",
    "Shopping Offers":    "Competitive follow-up + proof-of-close messaging",
    "Title / Legal Issue":"Assign title research / TC review",
    "Tenant / Access":    "Access plan + seller/tenant follow-up",
    "Long-Term Nurture":  "30 / 60 / 90-day nurture based on timeline",
    "Pass":               "Record pass reason; stop tasks or long-term review",
}

# Classifications where a photo/video package is expected (Blueprint §6/§7).
_VIABLE = {"Ready Now", "Wants More Money", "Family Decision", "Shopping Offers"}


def documentation_score(debrief, media, memo_present):
    """Blueprint §11 seven-item score. Each item -> Yes / No / Not Required."""
    disp = debrief.get("classification", "")
    media_required = disp in _VIABLE
    has_photos = bool(media.get("photos"))
    has_video = bool(media.get("video"))

    def req(present):
        if not media_required:
            return "Not Required"
        return "Yes" if present else "No"

    return {
        "Voice memo received":  "Yes" if memo_present else "No",
        "Visit outcome recorded": "Yes" if debrief.get("entered") is not None else "No",
        "Seller classified":    "Yes" if disp else "No",
        "Photos uploaded":      req(has_photos),
        "Video uploaded":       req(has_video),
        "Next action assigned": "Yes" if debrief.get("next_action") else "No",
        "Follow-up date set":   "Yes" if debrief.get("follow_up_date") else "No",
    }


def build_note(visit, debrief, media, score):
    """Compose the HTML note posted to REI (Blueprint §8 debrief fields)."""
    m = debrief
    def row(label, val):
        return f"<li><b>{label}:</b> {val}</li>" if val not in (None, "", []) else ""
    photos = media.get("photos") or []
    video = media.get("video")
    media_line = []
    if video:
        media_line.append(f'<a href="{video}">Walkthrough video</a>')
    if photos:
        media_line.append(f"{len(photos)} photo(s)")
    media_txt = " &middot; ".join(media_line) if media_line else "None found in Drive folder"

    missing = [k for k, v in score.items() if v == "No"]
    flag = ("<p style='color:#b23b31'><b>&#9888; Missing:</b> "
            + ", ".join(missing) + "</p>") if missing else ""

    return (
        f"<p><b>AUTO POST-VISIT DEBRIEF &mdash; {visit['address']}</b><br>"
        f"<i>Visit {visit.get('end_time','')} &middot; Seller: {visit.get('seller','')}</i></p>"
        "<ul>"
        + row("Entered property", "Yes" if m.get("entered") else "No")
        + row("Disposition", m.get("disposition"))
        + row("Classification", m.get("classification"))
        + row("Seller asking price", m.get("asking_price"))
        + row("Our likely offer", m.get("offer_range"))
        + row("Top repair concerns", m.get("repairs"))
        + row("Motivation / urgency", m.get("motivation"))
        + row("Decision maker", m.get("decision_maker"))
        + row("Objection", m.get("objection"))
        + row("Next action", m.get("next_action"))
        + row("Documentation", media_txt)
        + "</ul>" + flag
    )


def run_visit(visit, deps, rei, dry_run=True):
    """Run the full pipeline for one completed visit. Returns a result dict."""
    address = visit["address"]
    contact_id = visit.get("contact_id")

    # 1. Juan's memo (the trigger's field judgment)
    transcript = deps.get_memo(address, visit.get("end_time"))
    memo_present = bool(transcript)

    # 2/3. Summarize + classify (no memo -> minimal debrief, will escalate)
    debrief = deps.summarize(transcript) if memo_present else {
        "entered": None, "classification": "", "next_action": "", "follow_up_date": ""}

    # 4. Media in the property's Drive folder
    media = deps.find_media(address) or {"photos": [], "video": None}

    # 5. Documentation score
    score = documentation_score(debrief, media, memo_present)

    # Compose the outputs
    note_html = build_note(visit, debrief, media, score)
    cls = debrief.get("classification", "")
    next_step = SELLER_CLASSES.get(cls, "")
    follow_up = debrief.get("follow_up_date") or _default_follow_up(visit)

    result = {
        "address": address, "contact_id": contact_id,
        "classification": cls, "next_step": next_step,
        "follow_up_date": follow_up, "score": score,
        "note_html": note_html, "written": False, "escalations": [],
    }

    # 6. Update REI (or preview under dry_run)
    if contact_id and not dry_run:
        rei.add_note(contact_id, note_html)
        if cls:
            rei.set_disposition(contact_id, cls)
        if next_step:
            rei.create_task(contact_id, f"Next step: {next_step}", follow_up)
        result["written"] = True

    # 7. Escalations (Blueprint §12)
    esc = []
    if not memo_present:
        esc.append("No voice memo — request a 60-second update from Juan (same day).")
    if cls in _VIABLE and score["Photos uploaded"] == "No":
        esc.append("Viable deal missing photos — ping Juan while still nearby.")
    if cls in _VIABLE and score["Video uploaded"] == "No":
        esc.append("Viable deal missing walkthrough video.")
    if not cls and memo_present:
        esc.append("Could not classify seller — Coordinator to classify by EOD.")
    if not contact_id:
        esc.append("No REI contact linked to this visit — create/link the contact.")
    result["escalations"] = esc
    if esc and not dry_run:
        deps.escalate(f"Post-visit gaps: {address}", "\n".join(esc))

    return result


def _default_follow_up(visit):
    """Next business day if the memo gave no date (Blueprint §12 default)."""
    end = visit.get("end_time")
    try:
        base = datetime.date.fromisoformat(str(end)[:10])
    except Exception:
        base = datetime.date.today()
    nxt = base + datetime.timedelta(days=1)
    while nxt.weekday() >= 5:  # skip Sat/Sun
        nxt += datetime.timedelta(days=1)
    return nxt.isoformat()
