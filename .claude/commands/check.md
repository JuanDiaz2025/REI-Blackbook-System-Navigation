---
description: The master "check" routine. When Marie types "check", process every new call (inbound + outbound, no filters) into a CALL SUMMARY note, then automatically evaluate and fire all the follow-up triggers for each call.
allowed-tools: Read, [REI BlackBook tools]
---

# check — process new calls + fire all triggers

When Marie types **check**, run this whole routine. Everything below is part of
"check" — there are NO separate keywords. For each new call, do the notes step,
then evaluate EVERY trigger and fire whichever ones apply.

## Step A — Find every touched contact (FULL SWEEP, no filters)
The recordings inbox alone MISSES touches — non-recorded calls (failed/short
connects, some outbound dials) and text-only touches never appear there. So each
check, sweep ALL THREE inboxes and UNION them by contact:
1. **Recordings** — `/profitdial/inbox/recordings` (recorded calls).
2. **Calls** — `/profitdial/inbox/calls` (all calls incl. non-recorded / inbound).
3. **Texts** — `/profitdial/inbox/texts` (text touches).
Take **every** contact touched since the last check — inbound AND outbound, all
lead lists, marketing/View/wrong-number included, calls AND texts. No date filter,
no lead-type filter. Use the actual current date; never hard-code a day.

### AGENT-OWNERSHIP GATE (who handled the call) — REQUIRED
Only note a call/touch that was **handled by one of OUR three reps: THEA (me,
id 143173), CHERRY (115834), or JUAN (112447).**
- **If the call was made/answered/responded to by ANY other agent — Genesis, Kyle,
  Jen, or anyone else — DO NOT note it and DO NOT touch that lead.** Skip it
  entirely and say so in the report.
- Outbound: check the call's `created_by`. Only 143173 / 115834 / 112447 qualify.
- Inbound (created_by is null): determine the rep from the transcript — our rep
  introduces themselves ("this is Thea/Cherry/Juan…"). If it's Thea/Cherry/Juan,
  note it; if it's Genesis or another agent, skip and don't touch.
- **NEVER skip an inbound call from one of OUR existing leads.** If the seller calls
  IN and the contact already has our history — prior CALL SUMMARY notes, a comp/
  offer note, an Appointment tag, or any sign this is a lead we've been working —
  ALWAYS process it, no matter who dialed them recently. The gate must NOT drop an
  inbound seller just because another agent (e.g. 146286) auto-dialed that number
  right before. The "skip another agent's lead" rule is for OUTBOUND calls that
  agent made — not for a seller choosing to call our line. (This is exactly how
  Tyanna Moore got wrongly skipped once — don't repeat it.)
- **NEVER skip a call one of OUR OWN reps placed (Thea/Cherry/Juan).** If Thea,
  Cherry, or Juan dialed the lead, ALWAYS write a note — even a no-answer, VM, or
  short/no-connect, and even if the contact carries Do Not Contact / Dead Lead /
  Remove-From-List tags. A call our rep made is us actively working the lead, so it
  gets documented. If the contact is DNC/Remove-tagged, do NOT silently skip —
  instead note the attempt AND add a **TAG REVIEW** flag so Marie can reconcile
  whether the tag is stale (she may be actively working it) or the dialer list needs
  scrubbing. Noting + flagging beats hiding it. (This is how Maureen Thatcher got
  wrongly skipped once — don't repeat it.) The only outbound calls that skip are
  ones made by ANOTHER agent (146286, etc.).
- Text-only touches: only note if the outbound side was sent by / on behalf of
  Thea, Cherry, or Juan; otherwise skip.
- This gate is in ADDITION to the existing teammate-dedupe rule (still skip a call
  another teammate already wrote a substantive note for).

If a specific lead is named/flagged (e.g. "put notes on Bob") but isn't in any
inbox, look them up directly by name/phone and pull their contact history — a
non-recorded call still shows in the contact's own call history even when no inbox
lists it. (The agent-ownership gate still applies unless I explicitly override it
for a named lead.)

For each contact, gather call history, notes, and the **text thread** (chat feed =
inbound + outbound). Transcribe each new recording; for a non-recorded call, log
the touch from the call metadata (direction/outcome) even though there's no audio.

## Step B — Write the CALL SUMMARY note (with dedupe)
For each new call, before posting, **check the contact's existing notes** — if a
CALL SUMMARY for this same call/day already exists (e.g. a teammate already wrote
one), **skip** to avoid a duplicate and say so. Otherwise post a note grouped as:

```
CALL SUMMARY – <Month D, YYYY>
Call:  [the call bullets — the standard ++ fields: Contact Result, Summary,
        Seller Motivation, Timeline, Price Expectation, Property Details,
        Objections/Concerns, Next Step, Lead Temperature]
Texts: [the text thread — full back-and-forth, our outbound, any inbound we
        haven't replied to (flag it), and texts sent between calls; "none since
        last note" if none]
```
Only use info actually in the call/transcript/texts/notes. Unstated = "Not
mentioned". Never fabricate. Notes append — never overwrite.

**Rep name normalization (IMPORTANT).** Our only reps are **THEA, CHERRY, and
JUAN**. THEA is on most calls, and the transcription constantly mis-hears her
name as Sia / Tia / Zia / Nia / Theo / Deo / Leo / Pia / Lia / Cia (and similar).
Any such variant IS THEA — always write **THEA**. Only write Cherry or Juan when
it's unmistakably that person. If unsure who the rep is, default to **THEA**.
Never write a mis-heard variant (Sia/Theo/etc.) into a note.

## Step C — Evaluate ALL triggers for the call
Run each of these against the call and fire whichever apply (all automatic, no
approval unless noted). Each has a detailed spec in its own file:

1. **cherry-comps** — call hands the numbers off to Cherry → Cherry "Run comps"
   (High, today) + Marie "Check if lead was already called by Miss" (Medium, today).
2. **cherry-followup** — lead is Cherry's to call, whether she has already called
   (answered / voicemail / no answer) OR hasn't called yet (especially then) →
   Marie "Remind Miss to circle back on [Lead]" (Medium, today).
3. **voicemail-followup** — lead unresponsive (voicemail OR no answer, no live
   conversation) → Marie "Follow up on [Lead] (unresponsive)" (Medium, next day).
4. **flag-kyle-booked-appointment** — a property visit is booked → Kyle "Booked
   appointment on [visit date]" (High, booking day) with the prep checklist.
5. **Marie confirmation reminders** — a property visit is booked → prepare Marie's
   day-before + day-of confirmation-call tasks (High). [Currently: preview and wait
   for Marie's approval before saving, unless she has switched this to auto.]

Always dedupe (one of each per lead per call/day); if an open matching task
already exists, skip it and say so.

## Step D — Report back
Summarize: each lead + outcome (hot/warm/cold, answered vs voicemail/no answer),
any notes skipped as duplicates, and every task created (assignee, priority, due
date) or awaiting approval.

**Always end with a SKIPPED list.** For every touch you did NOT note this run, show
the lead name + the reason (agent-146286 outbound, wrong number, telemarketer/vendor,
hang-up/no content, duplicate note, etc.). This makes dropped leads visible so Marie
can eyeball them instead of having to remember names — if any skip looks wrong, she
says so and I pull it. Never silently drop a touch; if it wasn't noted, it appears
on the SKIPPED list with a reason.

## Teammate IDs (REI)
Cherry Hombre = 115834 · Theavil Marie (me) = 143173 · Kyle Flores = 146123 ·
Juan Diaz = 112447. Endpoint: POST /profitdial/actions/createTasks. Priority
High = real_priority 1, Medium = 3. REI has no task-edit and rejects past due dates.
