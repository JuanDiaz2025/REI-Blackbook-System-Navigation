---
description: Create a High-priority Cherry "Run comps" task for EVERY new incoming lead (proactively, before contact) so a preliminary offer is ready on the first live call — and also at any call that hands the numbers off to Cherry (which additionally makes Marie's "check if already called" task).
allowed-tools: Read, [REI BlackBook tools]
---

# Flag Cherry to run comps

Two ways this fires: **(A) proactively on every new incoming lead**, and **(B) at a
call that hands numbers to Cherry**. Create Cherry's "Run comps" task in BOTH cases.

## Trigger A — EVERY new incoming lead (proactive, no contact needed)
For each NEW lead that comes into REI — web-form submission, inbound call/text, new
mailer/PPC contact, any freshly-created seller contact — create Cherry's "Run comps"
task **right away, even if we have NOT reached them yet**. Goal: have comps + a
preliminary number ON RECORD in advance, so the moment we get them on a live call we
can quote a preliminary offer immediately instead of making them wait.
- This applies whether or not the lead has answered — cold, unreached leads included.
- **Needs a property address.** If the new lead has an address (web forms usually
  do), create the task. If there's no address yet, note that comps are blocked
  pending the address (Cherry can't comp without one) and flag it to get the address.
- Not a seller (wrong number, vendor/wholesaler, opt-out, do-not-contact, clearly
  out of our area) → do NOT create a Run comps task.

## Trigger B — a call hands numbers off to Cherry (existing)
Also fire when a call hands the lead's numbers to Cherry — rep says a colleague /
Cherry will call to run numbers, qualify, or give a preliminary/final offer
("Cherry will call you", "she'll run the numbers", "run comps", etc.).

Only Trigger B additionally makes Marie's "check if already called by Miss" task
(Step 2). Trigger A (a brand-new, not-yet-called lead) makes ONLY Cherry's Run comps
task — there's no prior call to dedupe, so skip Step 2 for Trigger A.

## Step 1 — Cherry's "Run comps" task  (fires for BOTH triggers)
Create ONE task on the seller's contact record:
- **Assign to:** Cherry Hombre
- **Title:** `Run comps`
- **Priority:** High
- **Due date:** today (arrival date for Trigger A, call date for Trigger B)
- **Linked to** the seller's contact/lead record
- **Description:** what Cherry needs to run comps and (once we've reached them) quote
  a preliminary offer — property address + seller name always, plus any price/
  condition context we already have (asking price, negotiable?, repairs, occupancy,
  timeline, best callback number, any tentative visit date). For a brand-new
  Trigger A lead with only a web-form address, that's fine — say "comps in advance,
  pre-contact; details TBD on first live call."
- **Dedupe: one Cherry "Run comps" task per lead, ever.** If any open "Run comps"
  task already exists for that seller (from an earlier proactive run OR a prior
  call), skip it and say so — don't stack a second one when a call later hands the
  same lead to Cherry.

## Step 2 — My "check" task  (Trigger B ONLY)
**Only for Trigger B** (a call handed the numbers to Cherry). Skip this entirely for
Trigger A — a brand-new, not-yet-called lead has no prior call to dedupe against.
Right after Cherry's task is created, create a SECOND task on the SAME contact:
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
Create BOTH tasks automatically (no preview/approval wait), same as the Cherry
task has always run.

## Report back
Seller + address · the trigger phrase matched · each task's assignee, priority,
and due date.

## Notes / implementation
- **Trigger A is independent of the note/agent-ownership gate.** `check` only writes
  CALL SUMMARY notes for calls handled by THEA/Cherry/Juan — but comps get assigned
  to EVERY new incoming seller lead regardless of who (if anyone) has talked to them.
  A lead with no call yet, or one another agent will handle, still gets a Run comps
  task under Trigger A. The gate governs notes, not comps.
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- Endpoint: POST /profitdial/actions/createTasks (direct JSON body, `item_ids`/
  `deal_id` = contact id — the reliable path; the contact-page modal silently fails
  on deal-linked contacts). Priority High = real_priority 1, Medium = 3. REI has no
  task-edit and rejects past due dates.
