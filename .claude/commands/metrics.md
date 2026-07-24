---
description: Theavil's daily performance scorecard. Every afternoon (before 5 PM Pacific), pull the full day's REI call log + tasks for Theavil (143173) and report the 9 daily metrics.
allowed-tools: Read, [REI BlackBook tools]
---

# Daily metrics — Theavil (id 143173)

Runs every afternoon before 5 PM Pacific (fired automatically by a Routine, or on
demand when Marie asks for "my metrics"). Covers **all calls made AND received**
that day. Report the 9 metrics below. Use the ACTUAL current date; never hard-code.

## Data sources (REI)
1. **Full call log** — `POST /profitdial/calls/getUserCallHistory`
   (form: `filters[archived__is][values]=0&offset=N&extraOffset=false&limit=100&order=c.id DESC&query_instance=inboxCallTableStore`).
   Page by offset until `created_at` rolls before today. Each call has:
   `created_by` (143173 = Theavil, 115834 = Cherry, 146123 = Kyle), `direction`,
   `status`, `duration`, `no_answer`, `left_voicemail`, `created_at`, `contact_id`,
   `first_name/last_name`, `recordings`. (See scratchpad `pull_calls.js`.)
2. **Tasks** — `POST /services/tasks/renderDataJson` (multipart, any contact_id,
   limit 400). Groups: `overdue`, `due_this_week`, `due_after_this_week`,
   `completed_tasks` (NOTE: completed feed is oldest-first & capped — same-day
   completions may not appear; report overdue=0 and queued/ due tasks instead).
   Filter by `assigned_to === "143173"`.
3. **Call outcomes** — transcribe recordings (faster-whisper small.en) to confirm
   live-vs-voicemail when duration is ambiguous. S3 links direct; Twilio links + `.mp3`.

## The 9 metrics
1. **New Lead Response Time** — for leads created today, minutes from lead/web-form
   creation to first outbound call or text. Report avg + examples. (Assumption:
   "response" = first call OR text.)
2. **Contact Rate** — live conversations ÷ dial attempts. Report BOTH by-dial and
   by-unique-lead. Live = a real two-way talk (confirm via transcript/duration),
   not VM/no-answer.
3. **Missed Calls Returned** — inbound calls not answered live (short/no-answer)
   that got a same-day callback. Exclude marketing/"View" spam.
4. **Qualified Leads** — motivated sellers reached today with property + price
   discussed (assumption; state it). Exclude declines/wrong numbers.
5. **Appointments Booked** — property visits booked/confirmed today (by Theavil).
   List lead + date/time.
6. **Follow-ups Completed** — follow-up tasks assigned to 143173 completed today.
   If the API cut can't confirm completions, report overdue count + tasks generated.
7. **CRM Accuracy** — were notes added for every touched lead; any data-quality
   issues (e.g. mis-heard rep names). Best-effort audit.
8. **Call Log Accuracy** — % of calls logged w/ timestamp + disposition + recording.
   Flag any call missing a recording.
9. **REI Completion Rate** — tasks assigned to 143173 due today: completed ÷ total;
   plus overdue count (0 = all obligations cleared).

## Rep names
Only THEA, CHERRY, JUAN. Any Sia/Tia/Zia/Nia/Theo/Deo/Leo/Pia/Lia/Cia = **THEA**.

## Format
Lead with a compact 9-row table (Metric | Result | Basis/assumption), then a short
"honest caveats" list for anything REI can't measure objectively. Note the day is
partial if run mid-afternoon. Offer a prior-day comparison.

## Teammate IDs
Cherry Hombre = 115834 · Theavil Marie = 143173 · Kyle Flores = 146123 · Juan Diaz = 112447.
