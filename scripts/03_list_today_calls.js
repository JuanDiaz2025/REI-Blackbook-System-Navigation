// Step 3: List today's calls from the ProfitDial call log, with contact IDs.
//
// Scrapes the Recordings tab (calls that produced audio — includes connected
// calls AND voicemails) and the Calls tab, then prints rows whose date matches
// the target day. Recorded outbound rows are the "leads you called today".
//
// Direction (inbound vs outbound) is NOT shown here — confirm it per-contact in
// step 4 (04_gather.js reads each call's `direction` field).
//
// Usage:
//   node scripts/03_list_today_calls.js            (defaults to today, local)
//   node scripts/03_list_today_calls.js "Jul 7"    (match a specific date label)

const { openContext, BASE } = require('./lib/browser');

function defaultLabel() {
  const d = new Date();
  const mon = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()];
  return `${mon} ${d.getDate()}`; // e.g. "Jul 7" — matches the log's "Jul 7, 9:59 AM"
}

async function scrape(page, url, label) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.waitForTimeout(6000);
  const rows = await page.$$eval('table tr', (trs) =>
    trs.map((tr) => {
      const cells = [...tr.querySelectorAll('td')].map((c) => (c.innerText || '').trim().replace(/\s+/g, ' '));
      const a = tr.querySelector('a[href*="/contacts/"]');
      const id = a ? (a.href.match(/contacts\/(\d+)/) || [])[1] : null;
      return { text: cells.join(' | '), id };
    }).filter((r) => r.text)
  );
  return rows.filter((r) => r.text.includes(label));
}

(async () => {
  const label = process.argv[2] || defaultLabel();
  const { ctx, page } = await openContext();
  try {
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(1500);
    for (const [name, path] of [
      ['RECORDINGS', '/profitdial/inbox/recordings'],
      ['CALLS', '/profitdial/inbox/calls'],
    ]) {
      const rows = await scrape(page, BASE + path, label);
      console.log(`\n==== ${name} matching "${label}" (${rows.length}) ====`);
      rows.forEach((r) => console.log(`  [${r.id || '--------'}] ${r.text}`));
    }
    console.log('\nGather the outbound contact IDs with: node scripts/04_gather.js <id> <id> ...');
  } finally {
    await ctx.close();
  }
})();
