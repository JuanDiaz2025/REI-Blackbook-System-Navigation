---
description: Automatically create a High-priority Cherry "Run comps" task for EVERY new incoming lead (any lead that reaches us via text OR call) at intake — no prompting, no waiting for contact — so comps and a preliminary offer are always on record ahead of time. Comps are assigned once, up front; a later call never needs to spin up a new Cherry task.
allowed-tools: Read, [REI BlackBook tools]
---

# Flag Cherry to run comps

**The rule:** every incoming lead gets ONE Cherry "Run comps" task, created
automatically at intake. Because that task already exists from the start, a later
call does NOT create another — it just relies on the comps already being on record.

## Trigger — EVERY incoming lead, at intake (the only trigger that creates the task)
The moment a lead comes into REI **through a text or a call** — inbound call/text,
web-form submission, new mailer/PPC contact, any freshly-created seller contact —
create Cherry's "Run comps" task **right away, automatically, before we've reached
them**. Goal: comps + a preliminary number ON RECORD in advance, so the instant we
get the seller on a live call we can quote a preliminary offer immediately instead
of making them wait.
- Applies whether or not the lead has answered — cold, unreached leads included.
- **"Incoming" = recent activity, NOT just a brand-new contact record.** A dormant or
  older lead that **re-engages** — replies to our outreach, texts/calls back in, or
  gets re-qualified (e.g. a fresh PropertyRadar/skip-trace hit today) — counts as an
  incoming lead and gets comps, even though the contact was created months/years ago.
  Scope the sweep by **recent touch/activity date, not `created_at`**, or reactivated
  leads (like a May-2025 contact who answers a July text) will be missed.
- **No prompting / no approval.** Don't ask first and don't preview — just create it.
- **Needs a property address.** If the lead has an address (web/inbound usually do),
  create the task. If there's no address yet, note that comps are blocked pending the
  address (Cherry can't comp without one) and flag it to get the address.

### Qualify from the message FIRST — read it before creating anything
Always read the actual inbound content (the text thread / SMS body, the voicemail or
call, the web-form fields) and decide if it's a real seller BEFORE making the task.
Do NOT blindly task every inbound number — a lot of inbound is not a valid lead.
- **CREATE the Run comps task when the message reads like a seller:** responding to
  our selling outreach, mentions their property / an address, asks about price, an
  offer, or a visit, gives condition/tenant/timeline details, or otherwise engages as
  an owner wanting to sell. A property address in the thread + any selling intent =
  valid. (Real examples: "one of the tenants at 7216 Eigleberry moved out, I'll be
  onsite Thursday"; "still working on Madeline to sell.")
- **SKIP — create NO task — when the message shows any of these:**
  - Opt-out / stop language: "STOP", "remove me", "do not contact", "unsubscribe".
  - Not selling: "not interested", "not selling", "already sold", "listed with an agent".
  - Wrong person: "wrong number", "who is this", "that's not my house", "you have the
    wrong Antonio", etc.
  - Not a seller at all: a vendor, wholesaler, or agent soliciting US; spam; a reply
    that's selling us something.
  - No property and no selling intent anywhere in the thread.
  - **Out of our area = outside California.** We buy statewide in CA — anywhere in
    California is in-area (Bay Area, Sacramento, Central Valley, SoCal, all of it).
    Only skip on geography when the property is in another state. If the state is
    unknown/not given, do NOT skip on location — treat it as in-area and proceed.
- **Ambiguous** (an auto-reply, a bare "?", a lone "ok" with no property, an empty
  11-second hang-up) → don't guess. Hold the task and flag it for a human to qualify,
  or wait for the address / a real reply. Better to hold than to task a non-lead.

## On a later call that "hands numbers to Cherry" — DON'T create a new task
When a call hands the lead's numbers to Cherry (rep says "Cherry will call you",
"she'll run the numbers", "run comps", etc.), the comps task should already exist
from intake — so **do not prompt or create a second Cherry task**. Just confirm the
intake "Run comps" task is there. Only if it is somehow missing (e.g. the lead
predates this rule), backfill ONE using Step 1. Never stack a duplicate.

On such a call, still create Marie's "check if already called by Miss" task (Step 2)
— that one is specific to the call handoff, not to comps.

## Step 1 — Cherry's "Run comps" task  (created once, at intake)
Create ONE task on the seller's contact record:
- **Assign to:** Cherry Hombre
- **Title:** `Run comps`
- **Priority:** High
- **Due date:** today (the day the lead came in)
- **Linked to** the seller's contact/lead record
- **Description:** what Cherry needs to run comps and (once we've reached them) quote
  a preliminary offer — property address + seller name always, plus any price/
  condition context we already have (asking price, negotiable?, repairs, occupancy,
  timeline, best callback number, any tentative visit date). For a brand-new lead
  with only an intake address, that's fine — say "comps in advance, pre-contact;
  details TBD on first live call."
- **Dedupe: one Cherry "Run comps" task per lead, ever.** If any "Run comps" task
  already exists for that seller (from intake OR a prior run), skip it and say so —
  never stack a second one, including when a later call hands the lead to Cherry.

## Step 2 — My "check" task  (call handoff ONLY)
**Only when a call hands the numbers to Cherry** (see the section above). Skip this
for the intake trigger — a brand-new, not-yet-called lead has no prior call to
dedupe against, so it gets ONLY the Run comps task.
Right after confirming Cherry's task exists, create a SECOND task on the SAME contact:
- **Assign to:** Theavil Marie (me)
- **Title:** `Check if lead was already called by Miss`
- **Priority:** Medium
- **Due date:** TODAY — the same date Cherry's task was created (NOT Cherry's due
  date, even if they ever differ).
- **Linked to** the same seller's contact/lead record.
- **Dedupe:** never more than one "Check if lead was already called by Miss" task
  per lead per call. If an open one already exists for that seller, skip it and
  say so.

## Automatic — no approval needed
Create the task(s) automatically (no preview/approval wait). The intake "Run comps"
task in particular is always fire-and-forget — never prompt before creating it.

## Report back
Seller + address · how the lead came in (text/call/web) · each task's assignee,
priority, and due date (or "comps blocked — no address yet").

## Notes / implementation
- **The intake comps task is independent of the note/agent-ownership gate.** `check`
  only writes CALL SUMMARY notes for calls handled by THEA/Cherry/Juan — but comps
  get assigned to EVERY new incoming seller lead regardless of who (if anyone) has
  talked to them. A lead with no call yet, or one another agent will handle, still
  gets a Run comps task at intake. The gate governs notes, not comps.
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- Endpoint: POST /profitdial/actions/createTasks (direct JSON body, `item_ids`/
  `deal_id` = contact id — the reliable path; the contact-page modal silently fails
  on deal-linked contacts). Priority High = real_priority 1, Medium = 3. REI has no
  task-edit and rejects past due dates.
