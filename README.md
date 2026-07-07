# REI-Blackbook-System-Navigation

Automation for the daily **called-leads review** in
[REI BlackBook](https://my.reiblackbook.com): sign in (with email 2FA), find the
leads called today, transcribe each call recording, and post a concise
`CALL SUMMARY` note to the lead's record.

## Why it exists

REI BlackBook stores call **recordings but no transcripts**, and its
answered/voicemail flags are unreliable. To summarize a call accurately you have
to listen to the audio — so this toolkit transcribes each recording offline and
turns it into a CRM-ready note in a fixed format.

## Quick start

```bash
cd scripts && npm install && python3 -m pip install -r requirements.txt && cd ..
cp scripts/config.example.env config.env   # fill in REI_EMAIL / REI_PASSWORD
set -a && . ./config.env && set +a

node   scripts/01_login.js                 # -> triggers email 2FA
node   scripts/02_verify.js "<link>"       # paste the emailed verification link
node   scripts/03_list_today_calls.js      # find today's calls + contact IDs
node   scripts/04_gather.js <id> <id> ...  # -> gathered.json
python3 scripts/05_transcribe.py           # -> transcripts.json
node   scripts/06_add_note.js <id> note.txt
```

## Docs

- [`docs/WORKFLOW.md`](docs/WORKFLOW.md) — full step-by-step runbook, prerequisites, guardrails.
- [`docs/NOTE_TEMPLATE.md`](docs/NOTE_TEMPLATE.md) — the CALL SUMMARY note format and how to classify a call.

## Security

Credentials, session cookies, seller PII, and call audio never get committed —
`config.env`, `.rei-profile/`, `gathered.json`, `transcripts.json`, and `rec/`
are all git-ignored. Transcription runs locally; audio is not sent to any API.
