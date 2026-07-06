# Runbook — Assisted run (Mode B)

These are the exact steps performed on each scheduled run inside the connected
Claude workspace. It uses the already-authorized connections; the only manual
input is an occasional REI verification link.

## Per-run steps

1. **Find completed visits.**
   List Google Calendar events whose title contains "Property Visit" and whose
   end time falls in the window since the last run. For each event, read from
   the description:
   - property **address** (event title)
   - **REI contact ID** (the `my.reiblackbook.com/contacts/<id>` link)
   - **seller name / phone**

2. **Get Juan's memo.**
   Search Voicenotes for a note mentioning that address, created around the
   visit time. Pull the transcript. (None yet → flag "no voice memo".)

3. **Summarize (Blueprint §8).**
   Extract: entered? · pursue/nurture/pass · asking price · our offer range ·
   repairs · motivation · decision-maker · objection · next action.

4. **Classify the seller (Blueprint §9).**
   One of: Ready Now · Wants More Money · Family Decision · Shopping Offers ·
   Title/Legal · Tenant/Access · Long-Term Nurture · Pass.

5. **Find media (Blueprint §7).**
   Search Drive for the address-named folder; separate walkthrough video from
   photos; note what's missing vs. the minimum package.

6. **Score documentation (Blueprint §11)** — the seven-item Yes/No/N-R score.

7. **Ensure REI session.**
   Reuse the saved session. If expired → **stop and notify the operator**:
   "REI session expired — send a fresh verification link," then wait.

8. **Update REI (contact ID from step 1).**
   - `add_note` — the debrief note + Drive media links
   - `set_disposition` — from the classification
   - `create_task` — the next step + follow-up date
   *(First live write is previewed for approval; dry-run until then.)*

9. **Log KPI row** to the *Property Visit Tracking* sheet (Blueprint §13):
   date, address, seller, classification, doc-score, media present, next step.

10. **Escalate gaps (Blueprint §12)** by email to Juan / the Coordinator:
    no memo · viable deal missing photos/video · unclassifiable · no next action.

## Schedule

A recurring trigger wakes this routine (hourly is the minimum cadence). Between
runs it is idle. Adjust or pause the cadence at any time.

## Operator inputs (rare)

- **REI verification link** — when the session expires (every few days). You'll
  get a clear prompt; paste the `.../emailLogin/<token>` URL and the run resumes.
