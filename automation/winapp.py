"""
Post-Visit Auto-Debrief — standalone Windows app (single-file, Flask + requests).

Double-click the built .exe: it opens a local dashboard in your browser. Type a
command like:

    Post debrief for 1185 Sterling Ave / Wayne Huber:
    <paste Juan's voice-memo text here>

and it will: find the REI BlackBook contact, summarize the memo with Claude,
and post the debrief NOTE + set the "Next Step" field + create a follow-up TASK.

Config (REI login, Anthropic key) is saved locally next to the app in
config.json — never uploaded anywhere. No Python needed once compiled to .exe.
"""

import os, sys, json, pickle, threading, webbrowser, re, datetime
from flask import Flask, request, jsonify, Response
import requests

REI = "https://my.reiblackbook.com"
APP_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
CONFIG = os.path.join(APP_DIR, "config.json")
SESSION = os.path.join(APP_DIR, "rei_session.pkl")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/141 Safari/537.36"
NEXT_STEP_PROFILE = "5289"
NEXT_STEP_FIELD = "crm_note_custom_field111151"

app = Flask(__name__)

def cfg():
    try: return json.load(open(CONFIG))
    except Exception: return {}
def save_cfg(d):
    c = cfg(); c.update(d); json.dump(c, open(CONFIG, "w"), indent=2)

def rei_session():
    s = requests.Session(); s.headers["User-Agent"] = UA
    if os.path.exists(SESSION):
        try: s.cookies.update(pickle.load(open(SESSION, "rb")))
        except Exception: pass
    return s
def save_session(s): pickle.dump(s.cookies, open(SESSION, "wb"))
def xhr(): return {"X-Requested-With": "XMLHttpRequest"}

def rei_authed(s):
    r = s.get(f"{REI}/services/account/", allow_redirects=True, timeout=30)
    return "login" not in r.url.lower()

# ---------- Claude (raw HTTP, no SDK) ----------
DEBRIEF_SYS = (
 "Extract a real-estate post-visit debrief from the operator's command + voice memo. "
 "Return ONLY JSON: {contact_query, address, seller, entered(bool|null), disposition, "
 "asking_price, offer_range, repairs, motivation, decision_maker, objection, next_action, "
 "follow_up_date(YYYY-MM-DD|null), classification(one of ['Ready Now','Wants More Money',"
 "'Family Decision','Shopping Offers','Title / Legal Issue','Tenant / Access',"
 "'Long-Term Nurture','Pass','TBD'])}. contact_query = the seller name or street address to "
 "search REI by. Use null/TBD when unknown. Do not invent facts.")

def claude_json(api_key, model, text):
    r = requests.post("https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": model or "claude-opus-4-8", "max_tokens": 1200,
              "system": DEBRIEF_SYS,
              "messages": [{"role": "user", "content": text}]}, timeout=90)
    r.raise_for_status()
    body = "".join(b.get("text", "") for b in r.json().get("content", []))
    body = body[body.find("{"): body.rfind("}") + 1]
    return json.loads(body)

# ---------- REI ops ----------
def rei_search(s, q):
    return s.get(f"{REI}/api/contacts/search", params={"q": q}, headers=xhr(), timeout=30).json()
def rei_add_note(s, cid, html):
    return s.post(f"{REI}/profitdial/contacts/addNote",
                  data={"contact_id": cid, "body": html}, headers=xhr(), timeout=45).json()
def rei_next_step(s, cid, text):
    f = NEXT_STEP_FIELD
    return s.post(f"{REI}/profitdial/profiles/saveProfileFieldValues/{NEXT_STEP_PROFILE}",
        data={"contact_id": cid, f+"[value]": text, f+"[type]": "crm_note",
              f+"[display_type]": "TextareaField", f+"[key]": "custom_field111151",
              f+"[relation_type]": "crm"}, headers=xhr(), timeout=45).json()
def rei_task(s, cid, title, desc, due):
    return s.post(f"{REI}/services/tasks/create",
        data={"contact_ids": cid, "title": title, "description": desc, "due_date": due},
        headers=xhr(), timeout=45).text

def build_note(d):
    row = lambda k, v: f"<li><b>{k}:</b> {v}</li>" if v not in (None, "", "TBD") else ""
    return ("<p><b>&#128203; AUTO POST-VISIT DEBRIEF &mdash; %s</b><br><i>Seller: %s</i></p><ul>"
        % (d.get("address") or "", d.get("seller") or "")
        + row("Entered property", "Yes" if d.get("entered") else ("No" if d.get("entered") is False else ""))
        + row("Disposition", d.get("disposition")) + row("Classification", d.get("classification"))
        + row("Asking price", d.get("asking_price")) + row("Our offer", d.get("offer_range"))
        + row("Repairs", d.get("repairs")) + row("Motivation", d.get("motivation"))
        + row("Decision maker", d.get("decision_maker")) + row("Objection", d.get("objection"))
        + row("Next action", d.get("next_action")) + "</ul>")

# ---------- HTTP routes ----------
@app.route("/")
def index(): return Response(PAGE, mimetype="text/html")

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        save_cfg(request.get_json(force=True) or {}); return jsonify(ok=True)
    c = cfg()
    return jsonify(REI_EMAIL=c.get("REI_EMAIL", ""),
                   has_pw=bool(c.get("REI_PASSWORD")), has_key=bool(c.get("ANTHROPIC_API_KEY")))

@app.route("/api/rei/status")
def api_status():
    try: return jsonify(authenticated=rei_authed(rei_session()))
    except Exception as e: return jsonify(authenticated=False, error=str(e))

@app.route("/api/rei/login", methods=["POST"])
def api_login():
    c = cfg(); s = rei_session()
    try:
        if rei_authed(s): return jsonify(status="authenticated")
        s.get(f"{REI}/services/account/login/", timeout=30)
        r = s.post(f"{REI}/services/account/login/", timeout=45, allow_redirects=True,
            data={"username": c.get("REI_EMAIL"), "password": c.get("REI_PASSWORD"),
                  "remember": "yes", "option": "com_users", "task": "user.login",
                  "return_on_error": "", "next": ""})
        if rei_authed(s): save_session(s); return jsonify(status="authenticated")
        if "checkEmail" in r.url or "Verify Your Email" in r.text:
            save_session(s); return jsonify(status="verification_needed")
        return jsonify(status="error", message="Login failed")
    except Exception as e: return jsonify(status="error", message=str(e))

@app.route("/api/rei/verify", methods=["POST"])
def api_verify():
    c = cfg(); s = rei_session(); link = (request.get_json(force=True) or {}).get("link", "").strip()
    try:
        s.get(link, timeout=45, allow_redirects=True)
        s.post(link, data={"executeLogin": "true"}, timeout=45, allow_redirects=True)
        if rei_authed(s): save_session(s); return jsonify(status="authenticated")
        return jsonify(status="error", message="Verification did not authenticate")
    except Exception as e: return jsonify(status="error", message=str(e))

@app.route("/api/command", methods=["POST"])
def api_command():
    c = cfg(); s = rei_session()
    text = (request.get_json(force=True) or {}).get("text", "").strip()
    dry = (request.get_json(force=True) or {}).get("dry_run", True)
    try:
        if not rei_authed(s): return jsonify(ok=False, error="Not logged in to REI — connect first.")
        d = claude_json(c.get("ANTHROPIC_API_KEY"), c.get("ANTHROPIC_MODEL"), text)
        q = d.get("contact_query") or d.get("seller") or d.get("address") or ""
        hits = rei_search(s, q) if q else []
        cid = hits[0]["id"] if hits else None
        note = build_note(d)
        nxt = d.get("next_action") or ""
        due = d.get("follow_up_date") or (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        result = {"contact_query": q, "contact_id": cid, "contact_name": hits[0]["name"] if hits else None,
                  "classification": d.get("classification"), "note_preview": re.sub("<[^>]+>", " ", note),
                  "next_step": nxt, "due": due, "written": False,
                  "candidates": hits[:5]}
        if cid and not dry:
            rei_add_note(s, cid, note)
            if nxt: rei_next_step(s, cid, nxt + (" | Classification: " + (d.get("classification") or "")))
            rei_task(s, cid, f"Next step: {nxt[:70]}", nxt, due)
            result["written"] = True
        elif not cid:
            result["error"] = "No REI contact matched — refine the name/address."
        return jsonify(ok=True, **result)
    except Exception as e:
        return jsonify(ok=False, error=str(e))

def _open(): webbrowser.open("http://127.0.0.1:5000/")

PAGE = """<!doctype html><html><head><meta charset=utf-8><title>Post-Visit Auto-Debrief</title>
<style>body{font-family:system-ui,Segoe UI,Arial;margin:0;background:#f5f3ef;color:#1b1e26}
header{background:#1b1e26;color:#fff;padding:14px 22px;font-weight:700}
header b{color:#d9591a}main{max-width:820px;margin:0 auto;padding:20px}
.card{background:#fff;border:1px solid #e3ddd3;border-radius:12px;padding:18px 20px;margin-bottom:16px}
h2{font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#8b90a0;margin:0 0 12px}
label{font-size:13px;font-weight:600;color:#555;display:block;margin:8px 0 3px}
input,textarea{width:100%;padding:9px 11px;border:1px solid #e3ddd3;border-radius:8px;font-size:14px;font-family:inherit}
textarea{min-height:150px}button{background:#d9591a;color:#fff;border:0;border-radius:8px;padding:10px 18px;font-weight:650;cursor:pointer;font-size:14px}
button:hover{background:#b8440f}.ghost{background:#fff;color:#1b1e26;border:1px solid #e3ddd3}
.pill{font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px}.ok{background:#e6f1ea;color:#2f7d55}.off{background:#f6e4e1;color:#b23b31}
.muted{color:#666;font-size:13px}.out{background:#faf9f6;border:1px solid #eee;border-radius:8px;padding:12px;white-space:pre-wrap;font-size:13px;margin-top:10px}
.row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.hide{display:none}</style></head><body>
<header><b>REI</b> Post-Visit Auto-Debrief</header><main>
<div class=card><h2>REI BlackBook</h2><div class=row><span id=pill class="pill off">checking…</span>
<button class=ghost onclick=chk()>Refresh</button><button onclick=login()>Log in</button></div>
<div id=vbox class=hide style=margin-top:10px><label>Paste the verification link REI emailed</label>
<input id=vlink placeholder="https://my.reiblackbook.com/services/account/emailLogin/..."><button style=margin-top:8px onclick=verify()>Complete login</button></div></div>
<div class=card><h2>Command → update REI</h2>
<label>Type your command + paste Juan's memo</label>
<textarea id=cmd placeholder="Post debrief for 1185 Sterling Ave / Wayne Huber:&#10;&#10;(paste the voice-memo text here)"></textarea>
<div class=row style=margin-top:10px><button onclick=run(true)>Preview</button><button onclick=run(false)>Post to REI</button></div>
<div id=out class=out style=display:none></div></div>
<div class=card><h2>Setup (one time)</h2><div class=muted>Saved locally in config.json.</div>
<label>REI email</label><input id=REI_EMAIL><label>REI password</label><input id=REI_PASSWORD type=password placeholder=••••••>
<label>Anthropic (Claude) API key</label><input id=ANTHROPIC_API_KEY type=password placeholder=••••••>
<button style=margin-top:12px onclick=savecfg()>Save setup</button> <span id=saved class=muted></span></div>
</main><script>
async function j(u,o){return (await fetch(u,o)).json()}
async function loadc(){const c=await j('/api/config');if(c.REI_EMAIL)REI_EMAIL.value=c.REI_EMAIL}
async function savecfg(){const b={};for(const k of['REI_EMAIL','REI_PASSWORD','ANTHROPIC_API_KEY']){if(document.getElementById(k).value)b[k]=document.getElementById(k).value}
await j('/api/config',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});saved.textContent=' ✓ saved';chk()}
async function chk(){pill.textContent='checking…';pill.className='pill off';const r=await j('/api/rei/status');
if(r.authenticated){pill.textContent='● Logged in';pill.className='pill ok';vbox.classList.add('hide')}else{pill.textContent='● Logged out';pill.className='pill off'}}
async function login(){const r=await j('/api/rei/login',{method:'POST'});if(r.status=='authenticated')chk();else if(r.status=='verification_needed')vbox.classList.remove('hide');else alert(r.message||r.status)}
async function verify(){const r=await j('/api/rei/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({link:vlink.value})});if(r.status=='authenticated')chk();else alert(r.message||r.status)}
async function run(dry){out.style.display='block';out.textContent='Working…';const r=await j('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:cmd.value,dry_run:dry})});
if(!r.ok){out.textContent='Error: '+(r.error||'');return}
out.textContent=(r.written?'✅ POSTED to REI\\n':'👁 PREVIEW (nothing posted)\\n')+'Contact: '+(r.contact_name||'(none matched)')+' ['+(r.contact_id||'-')+']\\nClassification: '+(r.classification||'')+'\\nNext step: '+(r.next_step||'')+'\\nDue: '+(r.due||'')+'\\n\\n'+(r.note_preview||'')+(r.error?('\\n\\n⚠ '+r.error):'')}
loadc();chk()</script></body></html>"""

if __name__ == "__main__":
    if "--no-browser" not in sys.argv: threading.Timer(1.2, _open).start()
    app.run(host="127.0.0.1", port=5000)
