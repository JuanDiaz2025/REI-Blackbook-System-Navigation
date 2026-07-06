# Post-Visit Auto-Debrief

Automation for the Equity Track **Post-Property Visit Conversion Process**.

When a property visit is completed, this turns Juan's one voice memo into a
full CRM update — with **no admin work from Juan**:

```
Calendar: a property-visit event finishes   ← the trigger
   ├─ read the REI contact ID (already in the event description)
   ├─ find Juan's Voicenote for that address → summarize into debrief fields
   ├─ find the photos + walkthrough video in the property's Drive folder
   ├─ update REI BlackBook: post the debrief note + set the next step
   ├─ log the row to the Property Visit Tracking sheet
   └─ if a viable deal is missing media/memo → email Juan / the Coordinator
```

The address is the key that ties everything together, and the calendar event
carries the REI contact ID directly — so no fragile address-search is needed.

---

## Two ways to run it

### Mode B — Assisted (available now, nothing to provision)
The pipeline runs **inside the connected Claude workspace**, which is already
authorized for Voicenotes, Google Drive/Calendar/Gmail, and REI BlackBook.
A schedule wakes it up; each run it processes any property visit that just
finished. See [`runbook.md`](runbook.md) for the exact per-run steps.

This is the fastest path to a working automation. Its only manual touch is the
REI verification link (below).

### Mode A — Standalone (own it / deploy it later)
The same logic packaged as a program you host yourself (cron on a small cloud
worker). It needs its **own** API credentials because a server cannot borrow
the Claude workspace's connections:

| Service | Credential needed |
|---|---|
| Google Calendar / Drive / Gmail | Google OAuth client + token (one covers all three) |
| Voicenotes | Voicenotes API token |
| Summarization | Anthropic (Claude) API key |
| REI BlackBook | account email + password (already have) |

Copy [`.env.example`](.env.example) to `.env` and fill these in.

---

## The REI login (important)

REI BlackBook has **no API**, so this talks to its internal web endpoints and
**requires an emailed verification link on each new session**. Because that
inbox isn't machine-readable here, the flow is:

1. The client reuses a saved session for as long as it stays alive (days).
2. When it finally expires, the run **stops and notifies you**:
   *"REI session expired — send a fresh verification link."*
3. You paste the link; the client finishes login and resumes. No password is
   ever shared with a third party.

So the REI link is an **occasional** step, not a per-run one.

---

## Safety: dry-run by default

`pipeline.run_visit(..., dry_run=True)` **previews** the REI note, next step,
and escalations without writing anything. Nothing is posted to a live seller
record until dry-run is turned off (and, on the first live run, the exact
content is shown for approval).

---

## Files

| File | What it is | Tested against live account |
|---|---|---|
| `rei_client.py` | REI BlackBook HTTP client (login/session, search, notes, add-note, disposition, task) | ✅ session-reuse, search, notes read |
| `pipeline.py` | Orchestration: summarize → score → note → next step → escalate | ✅ dry-run on a real memo |
| `runbook.md` | Step-by-step for the assisted (Mode B) run | — |
| `.env.example` | Config for the standalone (Mode A) deployment | — |

> The write calls (`add_note`, `set_disposition`, `create_task`) are mapped
> from REI's app bundle. Their exact optional fields (disposition IDs, task
> options) are confirmed on the **first approved live write**, then locked in.
