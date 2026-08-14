# Job: Daily Agent KPI Report — REI Blackbook

**Scope fence:** This job is metrics only. Do not write call narratives, call
summaries, disposition notes, or subtask breakdowns — that is `call-summary.md`'s
job. If asked for narrative, decline and point at the other job. Stay in your
lane.

**System:** REI Blackbook (REI-Blackbook-System-Navigation)
**Timezone:** California / America/Los_Angeles.
**Shift window:** 8:00am–5:00pm PT.
**Reporting window:** trailing 21 calendar days ending yesterday, unless a date
range is specified in the invocation.

## Inputs

Pull from REI Blackbook for every agent in scope (or the single agent named in
the invocation). For each agent you need, per calendar date:

| # | Column header (use verbatim) | Notes |
|---|------------------------------|-------|
| 1 | Date | Mmm DD format, e.g. `Aug 13` |
| 2 | Day | Three-letter weekday, e.g. `Thu` |
| 3 | Outbound dials | Agent-attributed |
| 4 | Inbound (team)† | Team-wide, NOT agent-attributed |
| 5 | Total calls‡ | Agent outbound + team inbound (blended) |
| 6 | Connects (≥30s) | Calls with ≥30 seconds of talk time |
| 7 | No-connect | |
| 8 | Talk time (h:mm:ss) | Format as `h:mm:ss`, never decimal hours |
| 9 | Unique leads | Distinct leads touched that day |
| 10 | Appts set* | Best-effort, see footnote |
| 11 | Offers / agrmts* | Best-effort, see footnote |
| 12 | Tasks completed | |
| 13 | Worked? | `Yes` if present, `Off` if not scheduled/no activity |

## Output

An `.xlsx` workbook named `agent-kpi_YYYY-MM-DD.xlsx`.

### Sheet 1 — Summary

One row per metric, mirroring the roll-up the CEO reads first:

| Metric | Total | Avg / present day |
|--------|-------|-------------------|

Include every numeric metric from the table above, in the same order. Carry the
†, ‡, and * markers into the metric labels here too, and reproduce the footnote
block at the bottom of this sheet. Add a `Present days: X of Y` line naming which
dates were off.

### Sheet 2 — Daily Breakdown (per date)

Reproduce the source layout exactly:

- **Title row** (merged, dark blue band, white bold): `{Agent Name} — Daily
  Breakdown (per date)`
- **Subtitle row** (merged, same band, smaller): `Agent {ID} • {Start} – {End},
  {Year} • California time (PDT), 8am–5pm shift`
- **Header row:** dark blue fill, white bold, wrapped, centered. Column headers
  verbatim from the table above.
- **Body:** one row per calendar date, ascending. Numbers centered.
- **Off-days:** grey fill, grey italic text, `Off` in the Worked? column, zeros
  across the metrics. Off-days are excluded from the average.
- **TOTAL row:** light blue fill, bold, live `SUM()` formulas across every
  numeric column. Worked? column shows `{N} days`.
- **AVG / present day row:** dark blue fill, white bold, live `AVERAGEIF()`
  formulas that divide by present days only — not calendar days.
- **Footnotes** below the table, small grey italic:
  - `† Inbound calls are logged without an answering-agent field — they cannot
    be attributed to one rep. Shown TEAM-WIDE for context, not credited to
    {Agent}.`
  - `‡ Total calls = {Agent} outbound + team inbound (blended; inbound not
    agent-split).`
  - `* Appointments & Offers are BEST-EFFORT: task title/keyword matches
    (appoint/booked/offer/agreement) on tasks {Agent} created or completed. May
    undercount — verify against CRM.`

### Sheet 3 — By Agent (multi-agent runs only)

One row per agent per date, same columns, so the team can be sorted and
filtered. Skip this sheet entirely on single-agent runs.

## Rules

- **Never invent a number.** Missing data → blank cell plus a note on Sheet 1.
  No interpolation, no "approximately."
- **Live formulas, not pasted values,** for every TOTAL and AVG cell.
- **Recalculate before delivering** so formula values populate. Verify zero
  `#REF!` / `#DIV/0!` / `#VALUE!` errors. The first LibreOffice run bootstraps
  its profile and is slow — allow generous timeout rather than killing it.
- **Talk time stays a duration.** `6:23:20`, not `6.39 hours`.
- **Averages divide by present days,** never by calendar days in the window.
- **Attribution honesty is non-negotiable.** Any metric that cannot be split by
  agent gets the † treatment and is labeled team-wide. Any keyword-inferred
  metric gets the * treatment. Do not quietly credit team activity to an
  individual — that is the single most damaging error this report can make.
- **No rows outside the stated range.** The header range and the body rows must
  agree. (The source workbook shows a stray `Jul 23` row above a stated
  `Jul 24 – Aug 13` window; it is correctly excluded from TOTAL, but it should
  not be rendered at all. Do not reproduce that quirk.)
- **Deliver the file.** Do not open a PR, do not commit to the repo.

## Schedule

Daily at 6:00 PM PT, immediately after the 8am–5pm shift closes.

- **Cron (UTC):** `0 1 * * *` — 6:00 PM PDT is 01:00 UTC the following day.
- **Note on PST:** when California drops to UTC-8 in November, this cron drifts
  to 5:00 PM local. Change it to `0 2 * * *` at the DST switch, or accept the
  one-hour shift.
- **Late-logging caveat:** activity logged after 6 PM will not appear in that
  day's run. The trailing-21-day window means it self-corrects the next day — so
  treat the most recent row as provisional and the rest as settled. Note this on
  Sheet 1.

## Scope

Default scope is **Agent 143173 (Theavil Marie)** only; Sheet 3 is skipped.

To widen to the full team, change this line to "all agents" and Sheet 3 turns
on.

## Invocation

**Default** (trailing 21 days, default scope):

> Read `jobs/agent-kpi.md` in the REI-Blackbook-System-Navigation repo and
> execute it.

**Custom range:**

> Read `jobs/agent-kpi.md` and execute it for Agent 143173, Jul 20 – Aug 13
> 2026.
