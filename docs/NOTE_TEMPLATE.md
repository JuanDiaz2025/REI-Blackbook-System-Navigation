# CALL SUMMARY note format

Every note added to a lead follows this exact structure. Keep it short, direct,
and CRM-ready. **Only include information found in the call activity, transcript,
texts, or existing notes.** Anything not stated = `Not mentioned` (or
`None mentioned` for objections). Never invent details.

```
CALL SUMMARY - <Month D, YYYY>

++ Contact Result: <Answered / No Answer / Voicemail / Disconnected / Wrong Number>
++ Summary: <short summary of what happened on the call>
++ Seller Motivation: <motivation or "Not mentioned">
++ Timeline: <timeline to sell or "Not mentioned">
++ Price Expectation: <amount or "Not mentioned">
++ Property Details: <condition, occupancy, tenants, repairs, etc. or "Not mentioned">
++ Objections/Concerns: <concerns or "None mentioned">
++ Next Step: <what should happen next>
++ Lead Temperature: <Hot / Warm / Cold / Not Qualified>
```

## Classifying Contact Result (from the transcript, not the metadata)

- **Answered** — a real two-way conversation with the seller/occupant.
- **Voicemail** — the recording contains a voicemail greeting ("can't take your
  call", "record your message") followed by a message we left.
- **No Answer** — rang out / hit an automated system with no message recorded.
- **Disconnected / Wrong Number** — number not in service, or the person reached
  is not the seller and has no connection to the property.

> The CRM's `no_answer` / `left_voicemail` flags are unreliable — we have seen a
> voicemail flagged as answered. Always decide from the transcript.

## Example (Antonio Ortiz, Jul 7 2026)

```
CALL SUMMARY - July 7, 2026

++ Contact Result: Voicemail (message left)
++ Summary: Outbound call went to voicemail. Tia (Twin Home Buyer) left a message checking in on the planned property visit (today/tomorrow) and asked Antonio to call back to receive a preliminary offer.
++ Seller Motivation: Not mentioned
++ Timeline: Not mentioned
++ Price Expectation: Not mentioned (preliminary offer to be given once seller calls back)
++ Property Details: Not mentioned on this call
++ Objections/Concerns: None mentioned
++ Next Step: Await callback; follow up to confirm property visit and present the preliminary offer.
++ Lead Temperature: Warm
```
