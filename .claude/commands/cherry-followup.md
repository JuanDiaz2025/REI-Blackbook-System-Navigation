---
description: After a call where Cherry actually calls the lead (answered, voicemail, or no answer), automatically create a same-day task for Marie to check/remind Miss to circle back on that lead.
allowed-tools: Read, [REI BlackBook tools]
---

# Follow-up after Cherry calls the lead

Review the call I just processed (the same call my notes command handled).

## Trigger
Act only if **Cherry herself placed / made the call to the lead** on this call —
regardless of the outcome. All of these count:
- **Answered** — Cherry spoke with the lead.
- **Voicemail** — Cherry left (or reached) the lead's voicemail.
- **No answer / didn't connect** — Cherry attempted the call but didn't reach anyone.

How to recognize it: the call is an outbound call from Cherry, or the transcript
has Cherry introducing herself / speaking as the Twin Home Buyer rep on the call
to the lead (e.g. "Hi, this is Cherry with Twin Home Buyer"). Inbound calls the
lead makes that merely get transferred to Cherry still count as Cherry reaching
the lead.

If Cherry did NOT call the lead on this call, do nothing and reply:
**"No Cherry call to the lead on this one."**

> This is SEPARATE from the `cherry-comps` command. That one fires at the moment
> a call hands the numbers off to Cherry (up front). THIS one fires AFTER Cherry
> has actually called the lead. Both can apply to the same lead on different
> calls — never delete or modify the cherry-comps behavior.

## The task to create
Create ONE task on the seller's contact record:
- **Assign to:** Theavil Marie (me) — id 143173
- **Title:** `Remind Miss to circle back on [Lead Name]`
- **Priority:** Medium (real_priority 3)
- **Due date:** TODAY — the date of Cherry's call (never a past date; REI rejects past due dates)
- **Linked to** the seller's contact/lead record
- **Description:** brief context — lead name + property address, the outcome of
  Cherry's call (answered / voicemail / no answer + one line on what happened),
  and the reminder purpose: check with / remind Miss to circle back on this lead.
- **Dedupe:** never more than one "Remind Miss to circle back" task per lead per
  Cherry call. If an open one already exists for that seller for the same call/day,
  skip it and say so.

## Automatic — no approval needed
Create the task automatically (no preview/approval wait), same as the
cherry-comps and Kyle flags run.

## Report back
Seller + address · Cherry-call outcome (answered / voicemail / no answer) · the
task's assignee, priority, and due date.

## Notes / implementation
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- "Miss" refers to the same teammate referenced in the cherry-comps command's
  "Check if lead was already called by Miss" task.
- Endpoint: POST /profitdial/actions/createTasks. Priority Medium = real_priority
  3. Assignee/priority are react-select (click current value, then the option).
  REI has no task-edit and rejects past due dates.
