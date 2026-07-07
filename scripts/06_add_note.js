// Step 6: Add a CALL SUMMARY note to a contact's Notes section.
//
// Reads a plain-text note file (the CALL SUMMARY template — see
// docs/NOTE_TEMPLATE.md), converts it to the HTML style REI BlackBook notes use,
// opens the contact's Add Note editor (TinyMCE), and saves. Verifies via the
// addNote2 response.
//
// The note file format: first line is the header ("CALL SUMMARY - <date>"),
// each following line starting with "++ Label: value" becomes a bolded-label
// bullet. Anything not stated on the call MUST be "Not mentioned" — do not invent.
//
// Usage: node scripts/06_add_note.js <contactId> path/to/note.txt

const fs = require('fs');
const { openContext, BASE } = require('./lib/browser');

function esc(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function toHtml(raw) {
  const lines = raw.replace(/\r/g, '').split('\n').map((l) => l.trim()).filter(Boolean);
  const header = lines.shift() || 'CALL SUMMARY';
  const bullets = lines.map((l) => {
    const m = l.match(/^\+\+\s*([^:]+:)(.*)$/);
    if (m) return `++ <strong>${esc(m[1])}</strong>${esc(m[2])}`;
    return esc(l);
  });
  return `<p>${esc(header)}</p>\n<p>${bullets.join('<br>\n')}</p>`;
}

(async () => {
  const id = process.argv[2];
  const file = process.argv[3];
  if (!id || !file) { console.error('Usage: node scripts/06_add_note.js <contactId> <note.txt>'); process.exit(1); }
  const html = toHtml(fs.readFileSync(file, 'utf8'));

  const { ctx, page } = await openContext();
  let saveResp = null;
  page.on('response', async (r) => {
    if (/addNote/i.test(r.url()) && r.request().method() === 'POST') {
      try { saveResp = { status: r.status(), body: (await r.text()).slice(0, 200) }; } catch {}
    }
  });
  try {
    await page.goto(BASE + '/contacts/' + id, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(9000);
    // open composer via the "Notes (NN)" panel + button
    const opened = await page.evaluate(() => {
      const heads = [...document.querySelectorAll('*')].filter(
        (e) => /^Notes\s*\(\d+\)/.test((e.innerText || '').trim()) && e.children.length < 4);
      if (!heads.length) return false;
      const h = heads[0];
      const area = (h.closest('div').parentElement) || h.closest('div');
      const hr = h.getBoundingClientRect();
      let best = null, bx = -1;
      area.querySelectorAll('button,a,svg,[role="button"]').forEach((b) => {
        const r = b.getBoundingClientRect();
        if (Math.abs(r.y - hr.y) < 40 && r.x > hr.x && r.x > bx) { bx = r.x; best = b; }
      });
      if (!best) return false;
      best.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      return true;
    });
    if (!opened) throw new Error('could not open Add Note composer');
    await page.waitForTimeout(3500);
    const via = await page.evaluate((h) => {
      if (window.tinymce && window.tinymce.activeEditor) {
        window.tinymce.activeEditor.setContent(h); window.tinymce.activeEditor.save(); return 'tinymce';
      }
      const f = document.querySelector('.tox-edit-area__iframe');
      if (f) { f.contentDocument.body.innerHTML = h; return 'iframe'; }
      return 'none';
    }, html);
    if (via === 'none') throw new Error('note editor not found');
    await page.waitForTimeout(800);
    await page.evaluate(() => {
      const b = [...document.querySelectorAll('button')].find((x) => /save note/i.test((x.innerText || '').trim()));
      if (b) b.click();
    });
    await page.waitForTimeout(6000);
    if (saveResp && /"success":true/.test(saveResp.body)) {
      console.log(`OK: note saved to contact ${id}.`);
    } else {
      console.log('WARN: could not confirm save. Response:', JSON.stringify(saveResp));
    }
  } finally {
    await ctx.close();
  }
})();
