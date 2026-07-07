// Step 4: Gather call history, texts, and existing notes for one or more contacts.
//
// Calls REI BlackBook's internal endpoints directly (authenticated via the cached
// session profile). Writes a single gathered.json and prints, per contact, the
// calls dated for the target day with direction + recording URL.
//
// Usage:
//   node scripts/04_gather.js <contactId> [contactId ...]
//   TARGET_DAY=2026-07-07 node scripts/04_gather.js 20463670
//
// Output: ./gathered.json   (consumed by 05_transcribe.py)

const fs = require('fs');
const { openContext, BASE } = require('./lib/browser');

function targetDay() {
  if (process.env.TARGET_DAY) return process.env.TARGET_DAY; // YYYY-MM-DD
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

(async () => {
  const ids = process.argv.slice(2);
  if (!ids.length) { console.error('Pass one or more contact IDs.'); process.exit(1); }
  const day = targetDay();
  const { ctx, page } = await openContext();
  try {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(1500);
    const out = {};
    for (const id of ids) {
      const hist = await page.request.post(BASE + '/profitdial/contacts/getContactHistoryById', {
        multipart: { id }, timeout: 60000,
      });
      const notes = await page.request.post(BASE + '/profitdial/contacts/getNotes/' + id, {
        multipart: { offset: '0', extraOffset: 'false', limit: '25' }, timeout: 60000,
      });
      const history = JSON.parse(await hist.text());
      out[id] = { history, notes: JSON.parse(await notes.text()) };

      const c = history.contact || {};
      const name = `${c.first_name || ''} ${c.last_name || ''}`.trim() || '(unassigned)';
      console.log(`\n=== ${id}  ${name}  ${c.phone1 || ''} ===`);
      (history.calls || [])
        .filter((x) => String(x.created_at || '').startsWith(day))
        .forEach((x) => {
          const rec = (x.recording || {}).link || '(no recording)';
          console.log(`  CALL ${x.created_at} | ${x.direction} | ${x.duration}s | rec: ${rec}`);
        });
      (history.texts || [])
        .filter((t) => String(t.created_at || '').startsWith(day))
        .forEach((t) => console.log(`  TEXT ${t.created_at} | ${t.direction} | ${(t.body || '').slice(0, 120)}`));
    }
    fs.writeFileSync('gathered.json', JSON.stringify(out));
    console.log('\nSaved gathered.json. Next: python3 scripts/05_transcribe.py');
  } finally {
    await ctx.close();
  }
})();
