# Daily "called leads" review — workflow runbook

Goal: for every lead **called today**, review the most recent call (activity,
recording, texts, existing notes), then post a concise `CALL SUMMARY` note to the
lead's Notes section in REI BlackBook.

This runbook + the `scripts/` folder let you (or an assistant) repeat the process.

---

## Prerequisites

```bash
cd scripts
npm install                 # Playwright
python3 -m pip install -r requirements.txt   # faster-whisper (offline transcription)
cp config.example.env ../config.env          # fill in REI_EMAIL / REI_PASSWORD
cd ..
set -a && . ./config.env && set +a
```

Notes:
- **Credentials** come from env vars only — never hard-code or commit them.
- **Offline transcription**: `faster-whisper` downloads a small model on first
  run. No third-party API or key is used; audio never leaves the machine.
- **Sandbox/proxy**: if you run this inside a proxied environment, also set
  `HTTPS_PROXY`, `NODE_EXTRA_CA_CERTS`, and `CHROMIUM_PATH` (see config example).
  On a normal laptop, leave those unset.

---

## The steps

### 1. Log in (triggers email 2FA)
```bash
node scripts/01_login.js
```
REI BlackBook emails a one-time verification link **on every login** (valid
~15 min). Credentials being accepted here already confirms they're valid.

### 2. Complete 2FA with the emailed link
Open the account inbox, copy the direct `my.reiblackbook.com/.../emailLogin/<token>`
link from the "REI BlackBook - Verify Login" email (not the sendgrid wrapper), then:
```bash
node scripts/02_verify.js "https://my.reiblackbook.com/services/account/emailLogin/<token>"
```
The link is bound to the login session cookie, so this **must** use the same
profile as step 1 (the scripts share `REI_PROFILE_DIR`). The session is then
cached — later steps don't re-authenticate.

### 3. Find today's calls
```bash
node scripts/03_list_today_calls.js            # or: ... "Jul 7"
```
Lists today's rows from the Recordings and Calls tabs with their contact IDs.
**Leads you called** = the *outbound* rows; inbound calls to unassigned marketing
numbers are not "leads you called" and are skipped. (Direction is confirmed in
step 4.)

### 4. Gather each lead's history, texts, and notes
```bash
node scripts/04_gather.js <id1> <id2> <id3> ...
```
Writes `gathered.json` and prints today's calls per contact with `direction`
(keep `outbound-dial` / `outbound-browser`), duration, and recording URL.

### 5. Transcribe today's recordings
```bash
python3 scripts/05_transcribe.py
```
Downloads each recording and transcribes it to `transcripts.json`. **This is the
only reliable source of what was said** — REI BlackBook stores audio but no
transcript, and the answered/voicemail flags can be wrong.

### 6. Draft and post each note
For each outbound lead, write a `note.txt` in the CALL SUMMARY format
(see `docs/NOTE_TEMPLATE.md`), sourcing every field only from the transcript /
texts / existing notes, then:
```bash
node scripts/06_add_note.js <contactId> note.txt
```
It opens the Add Note editor, saves, and confirms via the `addNote2` response.
Re-open the contact to eyeball the new note if you want a visual check.

---

## Scope & guardrails

- Only leads with **call activity today** get a note. Don't touch older leads.
- Only **outbound** calls (leads *you* called) — not inbound marketing calls.
- Never write a field that wasn't actually said → use `Not mentioned`.
- Writing notes changes the live CRM. When in doubt on an ambiguous call, review
  the transcript/recording before posting.

## Data hygiene

`gathered.json`, `transcripts.json`, `rec/`, `.rei-profile/`, and `config.env`
are git-ignored — they contain seller PII, call audio, and the login session.
Keep them local.
