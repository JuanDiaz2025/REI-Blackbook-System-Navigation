---
description: Part of "check". Whenever a processed call is UNRESPONSIVE — voicemail OR no answer (no live conversation with the lead) — automatically create a next-day follow-up task assigned to Marie.
allowed-tools: Read, [REI BlackBook tools]
---

# Next-day follow-up on unresponsive leads

Runs automatically as part of the normal **check** — no separate keyword needed.
For each call the check processes, also apply this rule.

## Trigger
Act whenever the lead was **unresponsive on this call — no live conversation**.
This covers BOTH:

- **Voicemail** — we reached the lead's voicemail (left a message or reached a
  greeting).
- **No Answer** — rang out, hit an automated system, mailbox full, line wouldn't
  accept the call, or the call dropped/disconnected before any conversation.

Do NOT fire when the lead actually **Answered** (a real two-way conversation), or
when it's a **wrong number / not-a-seller / do-not-call**.

If the lead was reached live (Answered) or it's a non-seller, do nothing and reply:
**"Lead was reached / not a seller — no follow-up task."**

## The task to create
Create ONE task on the seller's contact record:
- **Assign to:** Theavil Marie (me) — id 143173
- **Title:** `Follow up on [Lead Name] (unresponsive)`
- **Priority:** Medium (real_priority 3)
- **Due date:** the NEXT DAY (the day after the call). Never a past date.
- **Linked to** the seller's contact/lead record
- **Description:** brief context — lead name + property address, the unresponsive
  outcome (voicemail / no answer + one line on what happened), and the purpose:
  follow up with this lead tomorrow since we couldn't reach them live.
- **Dedupe:** never more than one "Follow up … (unresponsive)" task per lead per
  day. If an open follow-up task already exists for that seller, skip it and say so.

## Automatic — no approval needed
Create the task automatically (no preview/approval wait), same as the other
check flags.

## Report back
Seller + address · unresponsive outcome (voicemail / no answer) · the task's
assignee, priority, and due date (next day).

## Notes / implementation
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- "Next day" = call date + 1 day. REI rejects past due dates, so always use a
  future date.
- Endpoint: POST /profitdial/actions/createTasks. Priority Medium = real_priority
  3. Assignee/priority are react-select (click current value, then the option).
