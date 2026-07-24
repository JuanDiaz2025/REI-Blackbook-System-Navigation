// Logs into REI Blackbook and pauses for a manually-entered 2FA/verification
// code so the run never requests more than one code per attempt.
//
// Usage:
//   cp .env.example .env   # fill in REI_LOGIN_URL / REI_EMAIL / REI_PASSWORD
//   npm install
//   npm run login
//
// Requires a display (or Xvfb) unless HEADLESS=true — 2FA pages are easiest
// to debug headed. Screenshots are written to ./screenshots at each step.

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { chromium } = require('playwright');

require('dotenv').config();

const LOGIN_URL = process.env.REI_LOGIN_URL;
const EMAIL = process.env.REI_EMAIL;
const PASSWORD = process.env.REI_PASSWORD;
const HEADLESS = process.env.HEADLESS === 'true';
const STORAGE_STATE_PATH = path.join(__dirname, '..', 'auth.json');
const SCREENSHOT_DIR = path.join(__dirname, '..', 'screenshots');

function requireEnv() {
  const missing = ['REI_LOGIN_URL', 'REI_EMAIL', 'REI_PASSWORD'].filter((k) => !process.env[k]);
  if (missing.length) {
    console.error(`Missing required env vars: ${missing.join(', ')}`);
    console.error('Copy .env.example to .env and fill in the values.');
    process.exit(1);
  }
}

function promptForCode(promptText) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => {
    rl.question(promptText, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function screenshot(page, name) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, `${name}.png`), fullPage: true });
}

async function main() {
  requireEnv();

  const browser = await chromium.launch({ headless: HEADLESS });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(LOGIN_URL, { waitUntil: 'domcontentloaded' });
    await screenshot(page, '01-login-page');

    // TODO: adjust these selectors after inspecting the real login form.
    const emailField = page.locator('input[type="email"], input[name*="email" i]').first();
    const passwordField = page.locator('input[type="password"]').first();

    await emailField.fill(EMAIL);
    await passwordField.fill(PASSWORD);
    await screenshot(page, '02-credentials-filled');

    await Promise.all([
      page.waitForLoadState('networkidle').catch(() => {}),
      page.locator('button[type="submit"], input[type="submit"]').first().click(),
    ]);
    await screenshot(page, '03-after-submit');

    // Detect a verification/2FA step. This only triggers the site to send
    // ONE code — we wait here rather than retrying or resubmitting.
    const codeField = page
      .locator(
        'input[name*="code" i], input[autocomplete="one-time-code"], input[placeholder*="code" i]'
      )
      .first();

    const sawCodeField = await codeField
      .waitFor({ state: 'visible', timeout: 15000 })
      .then(() => true)
      .catch(() => false);

    if (sawCodeField) {
      console.log('\nA verification code has been requested (check email/SMS).');
      const code = await promptForCode('Paste the verification code (or link) here: ');
      const codeValue = extractCode(code);

      await codeField.fill(codeValue);
      await screenshot(page, '04-code-filled');

      await Promise.all([
        page.waitForLoadState('networkidle').catch(() => {}),
        page.locator('button[type="submit"], input[type="submit"]').first().click(),
      ]);
    }

    await screenshot(page, '05-final-state');

    const loggedIn = !page.url().includes('login');
    if (loggedIn) {
      await context.storageState({ path: STORAGE_STATE_PATH });
      console.log(`Login appears successful. Landed on: ${page.url()}`);
      console.log(`Session saved to ${STORAGE_STATE_PATH} for reuse by check-access.js`);
    } else {
      console.log(`Still on a login-related URL: ${page.url()}`);
      console.log('See screenshots/ for what the page looked like at each step.');
    }
  } finally {
    await browser.close();
  }
}

// Accepts either a bare code or a full verification link containing ?code=...
function extractCode(input) {
  try {
    const url = new URL(input);
    const fromQuery = url.searchParams.get('code');
    if (fromQuery) return fromQuery;
  } catch {
    // not a URL, fall through
  }
  return input;
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
