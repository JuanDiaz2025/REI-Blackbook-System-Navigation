// Step 1: Log in and trigger REI BlackBook's email 2FA.
//
// REI BlackBook requires email verification on every new login. This script
// submits your credentials, which causes REI BlackBook to email a one-time
// verification link (valid ~15 min) to the account address. It then stops.
//
// Next: read that link from the inbox and run 02_verify.js <link>.
//
// Env: REI_EMAIL, REI_PASSWORD (never hard-code these).
//
// Usage: node scripts/01_login.js

const { openContext, BASE } = require('./lib/browser');

(async () => {
  const email = process.env.REI_EMAIL;
  const password = process.env.REI_PASSWORD;
  if (!email || !password) {
    console.error('Set REI_EMAIL and REI_PASSWORD env vars first.');
    process.exit(1);
  }
  const { ctx, page } = await openContext();
  try {
    await page.goto(BASE + '/services/account/login/?', {
      waitUntil: 'domcontentloaded',
      timeout: 60000,
    });
    await page.fill('#modlgn_username', email);
    await page.fill('#modlgn_passwd', password);
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {}),
      page.click('button[type="submit"], input[type="submit"]').catch(() => page.keyboard.press('Enter')),
    ]);
    await page.waitForTimeout(4000);
    const url = page.url();
    const text = (await page.evaluate(() => document.body.innerText)).slice(0, 200).replace(/\s+/g, ' ');
    if (/checkEmail/i.test(url)) {
      console.log('OK: credentials accepted. Email 2FA required.');
      console.log('   Read the verification link from the inbox, then run:');
      console.log('   node scripts/02_verify.js "<verification-link>"');
    } else if (/login/i.test(url)) {
      console.log('LOGIN FAILED (still on login page). Check credentials.');
    } else {
      console.log('Logged in without 2FA prompt. URL:', url);
    }
    console.log('Page:', text);
  } finally {
    await ctx.close();
  }
})();
