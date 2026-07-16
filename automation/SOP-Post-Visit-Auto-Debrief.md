# SOP — Post-Visit Auto-Debrief (Equity Track)

**Owner:** Juan (Twin Home Buyer)
**System:** REI BlackBook ⇄ Google Calendar ⇄ Voicenotes ⇄ Google Drive
**Mode:** Scheduled, POST-IMMEDIATELY (do not hold for a "complete" memo)

---

## 1. Purpose

After every in-person property visit, turn Juan's field notes into a structured
debrief inside the seller's REI BlackBook contact — automatically, within the
same day — so no lead goes cold waiting on manual write-up. Each run:

1. finds visits that have already ended,
2. finds the matching voice recording,
3. posts a debrief note + sets the Next Step + creates a follow-up task on the
   REI contact,
4. attaches any Drive media (walkthrough video / photos),
5. escalates gaps (viable deal missing media, unclassifiable seller).

---

## 2. What ties the systems together

The **property address** is the join key across all four systems:

```
Google Calendar (the visit)  ──address──▶  Voicenotes (the recording)
        │                                          │
     contact_id                                 address
        ▼                                          ▼
   REI BlackBook (the note)  ◀──address──   Google Drive (video/photos)
```

- **Calendar** gives the visit, the address, the seller, and the REI
  `contact_id` (from the `my.reiblackbook.com/contacts/<id>` link in the event
  description).
- **Voicenotes** holds Juan's spoken debrief. Transcription garbles street
  names — always fuzzy-match:
  | Spoken / correct | Transcribes as |
  |---|---|
  | Chanslor | Chancellor |
  | Overacker | Over Cracker |
  | Tourbrook / Toure Brook | Tour Brook / Turbrook |
  Match on any distinctive token (street stem, seller first name, city).
- **Drive** holds the media, in a folder named for the address.
- **REI BlackBook** is the destination (note + Next Step field + task).

---

## 3. Trigger

A recurring schedule fires the run during daytime hours. Each firing is
independent and stateless except for `automation/processed.json` (the dedupe
ledger). Between runs the routine is idle.

---

## 4. Per-run procedure

### Step 1 — Find completed visits
List today's Google Calendar events that are property visits (title contains
`Property Visit`, `Appointment`, `Site Visit`, or an address) **whose END time
has already passed**. Skip anything still in progress or in the future.

For each, read:
- **address** (event title),
- **seller name / phone** (description),
- **REI contact_id** — from the `my.reiblackbook.com/contacts/<id>` link if
  present; otherwise look it up:
  `GET /api/contacts/search?q=<seller name or address>` (curl, saved cookie jar).

### Step 2 — Find the recording
Search Voicenotes (`search_notes` + `list_notes`) for any recording mentioning
the address or seller, applying the fuzzy-match rules in §2.

### Step 3 — Dedupe by recording
`automation/processed.json` stores each handled recording as `"vn:<uuid>"`.
- uuid already present → **skip**.
- A **new** recording for a property (even one posted before) → treat as an
  **UPDATE**: post a fresh note to the **same** REI contact.

### Step 4 — Post immediately (do NOT wait for a "complete" memo)
For each new recording:

**a. Summarize** into the debrief fields (mark unknowns `TBD`). Best-effort
seller classification (§6). If it's only an arrival/exterior memo, prefix the
note title **"(ARRIVAL/EXTERIOR — interior pending)"**.

**b. Find media** — search Drive for the address folder; include links to the
walkthrough video and photos if found.

**c. Verify REI session** via the saved cookie jar (`/tmp/reijar.txt`).
> **If the session is EXPIRED: STOP.** Message Juan exactly:
> `REI session expired — please send a fresh verification link`
> then wait. Do not attempt anything else until the link arrives.

**d. Write to REI** (curl, cookie jar) — three calls:
- **Add note** — the debrief HTML.
- **Set the Next Step field** (see §5 for the exact nested form).
- **Create a follow-up task**.

**e. Record & confirm** — append `"vn:<uuid>"` to `processed.json`, and confirm
to Juan: **address, contact id, note id**.

### Step 5 — Escalate gaps
Call out in the run summary: a viable deal missing photos/video, or a seller you
cannot classify.

---

## 5. REI BlackBook API cheat-sheet (curl + cookie jar)

All calls go through the proxy with the CA bundle:
```
curl -s --cacert /root/.ccr/ca-bundle.crt -b /tmp/reijar.txt \
     "https://my.reiblackbook.com/<endpoint>" ...
```

| Action | Method + endpoint |
|---|---|
| Session-alive / read fields | `GET /profitdial/profiles/getProfileFieldValues/5289?contact_id=<id>` |
| Search contact | `GET /api/contacts/search?q=<query>` |
| Add note | `POST /profitdial/contacts/addNote` — `contact_id`, `body` (HTML) → `{"success":true,"model_id":"<noteid>"}` |
| Read notes | `GET /contacts/getNotes/<contact_id>` |
| Create task | `POST /services/tasks/create` — `contact_ids`, `title`, `description`, `due_date` |

### The Next Step field (the tricky one)
Write to `POST /profitdial/profiles/saveProfileFieldValues/5289` with the value
sent as **nested** form fields (a flat string fails silently):

```
contact_id=<id>
crm_note_custom_field111151[value]=<the next step text>
crm_note_custom_field111151[type]=crm_note
crm_note_custom_field111151[display_type]=TextareaField
crm_note_custom_field111151[key]=custom_field111151
crm_note_custom_field111151[relation_type]=crm
```

Read it back at
`getProfileFieldValues/5289 → profileFieldValues.crm_note.data.custom_field111151.value`.

---

## 6. Seller classification → Next Step

| Classification | Next Step |
|---|---|
| Ready Now | Same-day offer / contract push |
| Wants More Money | Price-objection sequence + market update |
| Family Decision | Family-decision follow-up sequence |
| Shopping Offers | Competitive follow-up + proof-of-close messaging |
| Title / Legal Issue | Assign title research / TC review |
| Tenant / Access | Access plan + seller/tenant follow-up |
| Long-Term Nurture | 30 / 60 / 90-day nurture based on timeline |
| Pass | Record pass reason; stop tasks or long-term review |

**Viable** (media package expected): Ready Now · Wants More Money ·
Family Decision · Shopping Offers. A viable deal with no photos/video → escalate.

---

## 7. Debrief note contents

- Entered property? (Yes/No)
- Disposition (pursue / nurture / pass)
- Classification (§6)
- Seller asking price
- Our likely offer range
- Top repair concerns
- Motivation / urgency
- Decision maker
- Objection
- Next action
- Documentation (Drive links, or "None found")
- ⚠ Missing: (auto-listed if any required field is blank)

---

## 8. State & files

| File | Role |
|---|---|
| `automation/processed.json` | Dedupe ledger. Calendar-event ids and `vn:<uuid>` recording ids already handled. **Gitignored runtime state.** |
| `/tmp/reijar.txt` | REI cookie jar (the persisted session). |
| `automation/rei_client.py` | Reference client — the endpoint contract above. |
| `automation/pipeline.py` | Reference implementation of the summarize→score→write flow. |

---

## 9. Failure handling

| Situation | Action |
|---|---|
| **REI session expired** | STOP; message Juan the exact line in §4c; wait for the link. |
| **Voicenotes unavailable** (`stream closed before response received`) | Retry on the next scheduled run. Flag the gap to Juan **once**; don't re-ping every run. REI writes are unaffected. |
| **No recording yet for an ended visit** | Nothing to post. Stay silent; re-check next run. |
| **No REI contact linked** | Search by seller/address; if still none, escalate to create/link the contact. |
| **Can't classify seller** | Post the note with `Classification: TBD` and escalate for same-day classification. |

---

## 10. Communication rules

- Message Juan **when**: a debrief is posted (address + contact id + note id), a
  verification link is needed, or a gap must be flagged.
- **Stay silent** when there are no new recordings.
- Never hold a debrief waiting for a "complete" memo — post what exists now,
  label partial memos, and update when a fuller recording appears.

---

## 11. Definition of Done (per recording)

- [ ] Recording matched to the right address/contact.
- [ ] `vn:<uuid>` not already in `processed.json`.
- [ ] REI session confirmed alive.
- [ ] Note posted (`model_id` captured).
- [ ] Next Step field set (nested form) and verified on read-back.
- [ ] Follow-up task created.
- [ ] Drive media linked, or absence noted/escalated.
- [ ] `vn:<uuid>` appended to `processed.json`.
- [ ] Juan confirmed: address, contact id, note id.
