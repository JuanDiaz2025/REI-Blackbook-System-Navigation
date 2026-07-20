---
description: Whenever a lead is Cherry's to call — whether she has already called (answered, voicemail, or no answer) OR hasn't called yet — automatically create a same-day task for Marie to check/remind Miss to circle back on that lead.
allowed-tools: Read, [REI BlackBook tools]
---

# Follow-up so Marie can remind Miss to circle back

Review the call/lead I just processed (the same one my notes command handled).

## Trigger
Act whenever the lead is one **Cherry is responsible for calling / circling back
on**. This fires in BOTH situations:

1. **Cherry has already called the lead** this cycle — any outcome counts:
   - Answered (Cherry spoke with the lead)
   - Voicemail (Cherry left / reached the lead's voicemail)
   - No answer / didn't connect (Cherry attempted but didn't reach anyone)

2. **Cherry has NOT called the lead yet** but is expected to — e.g. the numbers
   were just handed to Cherry, a "Run comps"/callback is pending, or the note's
   Next Step is "Cherry to call". **ESPECIALLY create the task in this
   not-yet-called case** — that's when Marie most needs the reminder to push Miss
   to circle back.

Recognize Cherry involvement from: an outbound call by Cherry, the transcript
showing Cherry as the rep ("Hi, this is Cherry with Twin Home Buyer"), a call
transferred to Cherry, or the lead being handed to / pending with Cherry.

Only skip (do nothing) if the lead has **no connection to Cherry at all** (Cherry
isn't involved and isn't expected to call). In that case reply:
**"No Cherry involvement on this lead."**

> This is SEPARATE from the `cherry-comps` command and never modifies it.
> cherry-comps fires at the hand-off moment and also makes its own "Check if lead
> was already called by Miss" task. THIS command additionally ensures Marie gets a
> same-day reminder to push Miss to circle back — regardless of whether Cherry has
> called yet. Both can apply to the same lead on different calls.

## The task to create
Create ONE task on the seller's contact record:
- **Assign to:** Theavil Marie (me) — id 143173
- **Title:** `Remind Miss to circle back on [Lead Name]`
- **Priority:** Medium (real_priority 3)
- **Due date:** TODAY — the date of the call/processing (never a past date; REI rejects past due dates)
- **Linked to** the seller's contact/lead record
- **Description:** brief context — lead name + property address, and the current
  Cherry status: either the outcome of Cherry's call (answered / voicemail / no
  answer + one line) OR "Cherry has NOT called this lead yet — needs to circle
  back." Purpose: remind / check with Miss to circle back on this lead.
- **Dedupe:** never more than one "Remind Miss to circle back" task per lead per
  processing cycle. If an open one already exists for that seller for the same
  day, skip it and say so.

## Automatic — no approval needed
Create the task automatically (no preview/approval wait), same as the
cherry-comps and Kyle flags run.

## Report back
Seller + address · Cherry status (already called w/ outcome, OR not called yet) ·
the task's assignee, priority, and due date.

## Notes / implementation
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- "Miss" refers to the same teammate referenced in the cherry-comps command's
  "Check if lead was already called by Miss" task.
- Endpoint: POST /profitdial/actions/createTasks. Priority Medium = real_priority
  3. Assignee/priority are react-select (click current value, then the option).
  REI has no task-edit and rejects past due dates.
