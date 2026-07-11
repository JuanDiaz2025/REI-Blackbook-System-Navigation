---
description: After a call that hands the numbers off to Cherry, automatically create a High-priority "Run comps" task for Cherry, then a same-day Medium task for Marie to check if the lead was already called.
allowed-tools: Read, [REI BlackBook tools]
---

# Flag Cherry to run comps

Review the call I just finished (the same call my notes command processed).

## Trigger
Act only if the call hands the lead's numbers off to Cherry — e.g. the rep says a
colleague / Cherry will call to run the numbers, qualify the property, or give a
preliminary/final offer. Trigger phrases include (not limited to): "Cherry will
call you", "I'll relay your contact to Cherry", "she'll run the numbers",
"run comps", "a colleague will call to qualify".

If no hand-off to Cherry is mentioned, do nothing and reply:
**"No Cherry hand-off on this call."**

## Step 1 — Cherry's "Run comps" task  (UNCHANGED)
Create ONE task on the seller's contact record:
- **Assign to:** Cherry Hombre
- **Title:** `Run comps`
- **Priority:** High
- **Due date:** today (the call date)
- **Linked to** the seller's contact/lead record
- **Description:** what Cherry needs to run comps and call back — property address,
  seller name, and all price/condition context from the call (asking price,
  negotiable?, repairs, occupancy, timeline, best callback number, any tentative
  visit date).
- **Dedupe:** never more than one Cherry "Run comps" task per lead per call. If an
  open "Run comps" task already exists for that seller, skip it and say so.

## Step 2 — My "check" task  (NEW)
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
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- Endpoint: POST /profitdial/actions/createTasks. Priority High = real_priority 1,
  Medium = 3. Assignee/priority are react-select (click current value, then the
  option). REI has no task-edit and rejects past due dates.
