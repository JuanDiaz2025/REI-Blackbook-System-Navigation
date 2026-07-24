// Reuses the session saved by rei-login.js to confirm access without
// logging in again (and without requesting another verification code).
//
// Usage: npm run check-access

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

require('dotenv').config();

const LOGIN_URL = process.env.REI_LOGIN_URL;
const STORAGE_STATE_PATH = path.join(__dirname, '..', 'auth.json');

async function main() {
  if (!fs.existsSync(STORAGE_STATE_PATH)) {
    console.error(`No saved session at ${STORAGE_STATE_PATH}. Run "npm run login" first.`);
    process.exit(1);
  }

  const dashboardUrl = new URL(LOGIN_URL).origin;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ storageState: STORAGE_STATE_PATH });
  const page = await context.newPage();

  try {
    await page.goto(dashboardUrl, { waitUntil: 'domcontentloaded' });
    const stillLoggedIn = !page.url().includes('login');
    console.log(`Current URL: ${page.url()}`);
    console.log(stillLoggedIn ? 'Access confirmed — session is still valid.' : 'Session expired — rerun "npm run login".');
    process.exit(stillLoggedIn ? 0 : 1);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
