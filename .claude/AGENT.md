# Twin Home Buyer — REI BlackBook AI Agent

One agent, one job: **work the pipeline every day and drive deals toward booked
visits and closings.** Marie types a keyword; the agent does the rest. All pieces
below are part of the same system.

## The daily loop
1. **`check`** — the heartbeat. Sweeps all 3 inboxes (Recordings + Calls + Texts),
   writes a CALL SUMMARY note for every touch, and fires all triggers. Run it as
   often as you like; each run only processes what's new.
2. **`metrics`** — the daily scorecard for Theavil (9 KPIs), built from the full
   call log + tasks. Meant for every afternoon before 5 PM.
3. **`close-deal`** — ranks the whole pipeline by deal-stage, picks the single most
   closeable deal, and drives it with tasks + a strategy note until it funds.

## Triggers fired inside `check` (auto)
- **cherry-comps** — numbers handed to Cherry → Cherry "Run comps" + Marie "Check if
  lead was already called by Miss".
- **cherry-followup** — lead is Cherry's to call → Marie "Remind Miss to circle back".
- **voicemail-followup** — unresponsive (VM/no answer) → Marie next-day follow-up.
- **flag-kyle-booked-appointment** — a visit is booked → Kyle prep task (High).

## Hard rules (apply everywhere)
- **Agent-ownership gate:** only note calls handled by **THEA (143173), CHERRY
  (115834), or JUAN (112447)**. Anything by Genesis/Kyle/Bryan/any other agent →
  skip, don't touch. (Outbound = `created_by`; inbound = who intros on the transcript.)
- **Rep name = THEA:** transcription mis-hears her as Sia/Tia/Zia/Nia/Theo/Deo/Leo/
  Pia/Lia/Cia — always write **THEA**. Only Cherry/Juan when unmistakable.
- **Never fabricate.** Unknown = "not surfaced yet." Notes append, never overwrite.
- **Task creation = DIRECT API** (`POST /profitdial/actions/createTasks`, JSON body,
  `item_ids`/`deal_id` = contact id). The contact-page modal silently fails on
  deal-linked contacts — the direct call is the reliable path.

## Teammate IDs
Cherry Hombre 115834 · Theavil Marie 143173 · Kyle Flores 146123 · Juan Diaz 112447.

## Two upgrades AWAITING Marie's approval (not yet live)
- **DEAL READ** — a blunt-analyst second pass on each `check` note (real motivation ·
  deal traps · a 2-sentence, no-price, visit-earning opener in Juan's voice).
- **drive-time** (`drive-time.md`) — office→property distance/ETA via the Google
  Routes API + a Maps link, on demand and inside the booking flow.
Both were previewed; save on Marie's "go."

## Autonomy (Marie's call)
The agent currently runs when Marie types a keyword. It can be made autonomous with
scheduled triggers (daily `check` sweeps, the 4 PM `metrics` scorecard, a daily
`close-deal` push). Off by default until Marie turns it on.
