---
description: After a call where a property visit (or tentative property visit) is set, create ONE high-priority task for JONATHAN ROSANES, titled in the "Booked appointment | phone | date time" format, with the prep checklist.
allowed-tools: Read, [REI BlackBook tools]
---

# Flag Jonathan for a booked appointment

Review the call I just finished (the same call my notes command processed).
(This task used to go to Kyle — it now goes to **Jonathan Rosanes**.)

## Trigger
Act if the call signals a **property visit / walkthrough is set for a specific date
— including a TENTATIVE visit**. Trigger phrases include (not limited to):
"appointment booked", "booked the appointment", "tentative visit", "let's set a
visit", "prepare docs", "visit is set", or any property visit (firm or tentative)
tied to a specific day/time.

If no visit (firm or tentative) is mentioned, do nothing and reply:
**"No booked appointment on this call."**

## On a booked / tentative visit
1. Get the **seller name** and **property address** from the call.
2. Get the **seller phone number** (the contact's best number) — for the task title.
3. Get the **visit date + time**. If I said it relative to the call ("Saturday
   7 AM", "next Tuesday at 2"), convert it to a real date using the call's date. If
   no clear date/time was stated, do NOT guess — ask me for the visit date + time.
4. Create **ONE** task in REI BlackBook on that seller's contact record:
   - **Assign to:** Jonathan Rosanes  (REI id 134735)
   - **Title (EXACT format):** `Booked appointment | [phone] | [date time]`
     - phone formatted like `(707) 481-3916`
     - date/time formatted like `August 05, 2026 7:00 AM`
     - Full example: `Booked appointment | (707) 481-3916 | August 05, 2026 7:00 AM`
   - **Description** (this exact layout — unchanged):
     ```
     [Lead name]
     Booked appointment / visit scheduled: [visit date time]
     [property address]

     * Create a WhatsApp group
     * Add to Juan's calendar
     * Prepare document - contract
     ```
   - **Priority:** High
   - **Due date:** the **day the appointment was booked** (the call date — normally
     *today*), NOT the visit date. This notifies Jonathan right away so he can prep
     ahead of the visit. NOTE: REI rejects past due dates; if the booking day is
     somehow before today, use today (the earliest allowed).
5. **Dedupe:** never create more than one booked-appointment task per lead per
   call. If an open "Booked appointment" task already exists for that seller,
   skip it and say so.

## Report back
Seller + address · phone · visit date + time · assigned to Jonathan · the exact
phrase you matched.

## Notes / implementation
- REI BlackBook has **no separate calendar-event object** — a due-dated task IS
  the calendar entry (it syncs out via **Calendar Sync**). So one due-dated task
  covers both the task and the calendar. Do not create a second "event" task.
- The **screen pop-up** on the visit day depends on Jonathan having **Calendar Sync
  turned on** in his REI settings (or a Google Calendar integration connected
  to the assistant). The task itself is always created regardless.
- Assignable teammate IDs (REI): Jonathan Rosanes = 134735, Kyle Flores = 146123,
  Cherry Hombre = 115834, Juan Diaz = 112447, Theavil Marie = 143173.
- Task creation endpoint: `POST /profitdial/actions/createTasks` (direct JSON body,
  `item_ids`/`deal_id` = contact id). Priority High = real_priority 1.
