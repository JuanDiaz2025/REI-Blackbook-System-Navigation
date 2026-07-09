---
description: After a call where a property visit is booked, create ONE high-priority task for Kyle, due on the visit date
allowed-tools: Read, [REI BlackBook tools]
---

# Flag Kyle for a booked appointment

Review the call I just finished (the same call my notes command processed).

## Trigger
Act only if I confirmed a **property visit / walkthrough is booked for a specific
date**. Trigger phrases include (not limited to): "appointment booked",
"booked the appointment", "prepare docs", "visit is set", or any property visit
set for a specific day.

If no booking is mentioned, do nothing and reply:
**"No booked appointment on this call."**

## On a booked visit
1. Get the **seller name** and **property address** from the call.
2. Get the **visit date**. If I said it relative to the call ("Saturday",
   "next Tuesday"), convert it to a real date using the call's date. If no clear
   date was stated, do NOT guess — ask me for the date.
3. Create **ONE** task in REI BlackBook on that seller's contact record:
   - **Assign to:** Kyle Flores
   - **Title:** `Booked appointment on [visit date]`
   - **Description:** `Seller: [name] | Visit date: [visit date] | Property: [address]`
   - **Priority:** High
   - **Due date:** the **visit date** (same day)
4. **Dedupe:** never create more than one booked-appointment task per lead per
   call. If an open "Booked appointment" task already exists for that seller,
   skip it and say so.

## Report back
Seller + address · visit date · assigned to Kyle · the exact phrase you matched.

## Notes / implementation
- REI BlackBook has **no separate calendar-event object** — a due-dated task IS
  the calendar entry (it syncs out via **Calendar Sync**). So one due-dated task
  covers both the task and the calendar. Do not create a second "event" task.
- The **screen pop-up** on the visit day depends on Kyle having **Calendar Sync
  turned on** in her REI settings (or a Google Calendar integration connected
  to the assistant). The task itself is always created regardless.
- Assignable teammate IDs (REI): Kyle Flores = 146123, Cherry Hombre = 115834,
  Juan Diaz = 112447.
- Task creation endpoint: `POST /profitdial/actions/createTasks`. Priority
  High = real_priority 1. Assignee dropdowns are react-select (set value, then
  pick the option). Deleting a task requires typing "Delete" in the confirm box.
