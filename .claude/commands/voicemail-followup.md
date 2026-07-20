---
description: Whenever a processed call is a voicemail (lead unresponsive — only reached/left voicemail, no live conversation), automatically create a next-day follow-up task assigned to Marie.
allowed-tools: Read, [REI BlackBook tools]
---

# Next-day follow-up on unresponsive (voicemail) leads

Review the call I just processed (the same call my notes command handled).

## Trigger
Act only if the lead was **unresponsive on this call — Contact Result is
Voicemail**: we reached the lead's voicemail (left a message, or reached a
voicemail greeting) and had **no live conversation** with the lead.

- This is about leads we **couldn't reach live**. A voicemail counts.
- Do NOT fire when the lead actually **Answered** (a real two-way conversation),
  or when it's a wrong number / not-a-seller / do-not-call.

If the call was not a voicemail, do nothing and reply:
**"Not a voicemail — no follow-up task."**

## The task to create
Create ONE task on the seller's contact record:
- **Assign to:** Theavil Marie (me) — id 143173
- **Title:** `Follow up on [Lead Name] (left voicemail)`
- **Priority:** Medium (real_priority 3)
- **Due date:** the NEXT DAY (the day after the call). Never a past date.
- **Linked to** the seller's contact/lead record
- **Description:** brief context — lead name + property address, that today's call
  went to voicemail (message left / mailbox reached), and the purpose: follow up
  with this lead tomorrow since they were unresponsive.
- **Dedupe:** never more than one "Follow up … (left voicemail)" task per lead per
  day. If an open follow-up task already exists for that seller, skip it and say so.

## Automatic — no approval needed
Create the task automatically (no preview/approval wait), same as the other flags.

## Report back
Seller + address · confirmed the call was a voicemail · the task's assignee,
priority, and due date (next day).

## Notes / implementation
- Assignable teammate IDs (REI): Cherry Hombre = 115834, Theavil Marie (me) =
  143173, Kyle Flores = 146123, Juan Diaz = 112447.
- "Next day" = call date + 1 day. REI rejects past due dates, so always use a
  future date.
- Endpoint: POST /profitdial/actions/createTasks. Priority Medium = real_priority
  3. Assignee/priority are react-select (click current value, then the option).
