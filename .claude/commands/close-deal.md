---
description: The deal-closer agent. Scan the ENTIRE REI pipeline, rank every lead by how close it is to closing, pick the single highest-probability deal, and drive it to the finish with concrete next-actions, drafts, and tasks — tracking daily until it funds.
allowed-tools: Read, [REI BlackBook tools]
---

# close-deal — drive at least one deal to close

Goal: get **at least one deal to CLOSED** using all the leads we have. The agent
orchestrates (analyze, prioritize, draft, task, track). Humans do the calls,
negotiation sign-off, and signatures — the agent tees them up and pushes daily.

## Step 1 — Rank the whole pipeline by closeness
Pull all contacts (`POST /profitdial/contacts/query`, limit 9000). Each contact's
`flags` array holds its tags. Score by stage (highest = closest to close):
1. **In escrow / closing date set** (notes say "in escrow", "closing <date>")
2. **Under Contract / Contract Signed / Signed Contract**
3. **Offer Pending / Negotiation / Negotiating**
4. **Offer Sent**
5. **Appointment Booked / Property Visit Pending**
Tag IDs (contactsTableStore/tags): Under Contract 382145 · Contract Signed 947562 ·
Signed Contract 947561 · Offer Pending/Negotiation 1162896 · Negotiating 540552 ·
Offer sent 970627 · Appointment Booked 609667 · Property Visit Pending 1163256.
EXCLUDE dead tags: Deal Closed, Sold*, Closed Lost, Dead Lead, DNC, Do Not Contact,
Not Interested, Seller Rejected offer, DECLINED OFFER, Listed with Agent, Already
Listed, Contract Fell Through, Canceled contract, Lost Deal, Not a viable deal,
Disqualified, Sold to Realtor/Competitor.

## Step 2 — Diagnose the top candidates
For the top ~6, read their latest notes and find the SINGLE blocker keeping each
from closing (e.g. title issue, payoff demand needed, credit/price standoff,
identity verification, unsigned doc, occupancy/tenant). Prefer deals where the
blocker is administrative/one-decision and a closing date is near.

## Step 3 — Pick THE one + make the close move
Choose the deal with the best (closeness × low-blocker × margin × timeline). For it:
- Post a **DEAL-CLOSER STRATEGY** note: current status, key numbers/margin, the one
  blocker, and a prioritized recommendation to remove it.
- Create push tasks (direct API — see below): a decision/action task for the owner
  (usually Juan 112447) with the exact recommendation, and a tracking task for Marie
  (143173) to confirm escrow/title/signatures and report daily until funded.
- If a message or counter is needed, DRAFT it for a human to send (never send to a
  seller directly).

## Step 4 — Track daily until funded
Each run, re-check the target's tags/notes for movement; update the tasks and a short
status line. Escalate if it stalls (blocker unresolved 2+ days) or flip to the next
best deal if this one dies. Done = the deal's tag flips to Deal Closed / funded.

## Task creation — use the DIRECT API (reliable)
`POST /profitdial/actions/createTasks`, JSON body:
`{title, description, due_date:"YYYY-MM-DD", type:"misc", assigned_to, real_priority,
due_time:"05:00 PM", time_zone:"America/Los_Angeles", recording_action_item_id:"",
item_ids:"<contactId>", deal_id:"<contactId>"}`. real_priority: High=1, Medium=3.
This bypasses the contact-page task modal, which silently fails on deal-linked contacts.

## Teammate IDs
Cherry Hombre 115834 · Theavil Marie (me) 143173 · Kyle Flores 146123 · Juan Diaz 112447.

## Honesty
The agent can't call, negotiate, or sign for anyone, and can't guarantee a seller
says yes. It guarantees the deal is correctly prioritized, the blocker is identified,
the exact next action is queued and tracked, and drafts are ready — so the human step
is as small as possible.
