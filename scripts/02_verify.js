// Step 2: Complete email 2FA using the verification link.
//
// IMPORTANT: this must run against the SAME persistent profile as 01_login.js,
// because REI BlackBook binds the verification link to the login session cookie.
// (Opening the link in a fresh/other browser just bounces back to the login page.)
//
// The link looks like:
//   https://my.reiblackbook.com/services/account/emailLogin/<token>
// Use the direct my.reiblackbook.com link from the email body, NOT the
// sendgrid click-tracking wrapper.
//
// Usage: node scripts/02_verify.js "<verification-link>"

const { openContext, BASE } = require('./lib/browser');

(async () => {
  const link = process.argv[2];
  if (!link || !/emailLogin/.test(link)) {
    console.error('Pass the my.reiblackbook.com/.../emailLogin/<token> link as an argument.');
    process.exit(1);
  }
  const { ctx, page } = await openContext();
  try {
    await page.goto(link, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    const url = page.url();
    if (/login/i.test(url)) {
      console.log('NOT authenticated — link may be expired/used, or profile mismatch.');
      console.log('Re-run 01_login.js to get a fresh link, then verify quickly.');
    } else {
      console.log('AUTHENTICATED. Session cached in the profile. URL:', url);
    }
  } finally {
    await ctx.close();
  }
})();
