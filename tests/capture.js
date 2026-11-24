const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function runTests() {
  console.log("Launching browser...");
  const browser = await puppeteer.launch({
    headless: "new",
    defaultViewport: { width: 1280, height: 800 }
  });
  const page = await browser.newPage();
  const logs = [];
  const networkRequests = [];
  
  page.on('console', msg => {
    if (msg.type() === 'error') logs.push(`[ERROR] ${msg.text()}`);
    else if (msg.type() === 'warning') logs.push(`[WARN] ${msg.text()}`);
    else logs.push(`[LOG] ${msg.text()}`);
  });

  page.on('request', req => {
    if (req.url().includes('/api/')) {
      networkRequests.push(`[REQ] ${req.method()} ${req.url()}`);
    }
  });
  
  page.on('response', async res => {
    if (res.url().includes('/api/')) {
      networkRequests.push(`[RES] ${res.status()} ${res.url()}`);
    }
  });

  try {
    console.log("Navigating to login page...");
    await page.goto('http://localhost:3000/login', { waitUntil: 'networkidle2' });
    await page.screenshot({ path: path.join(__dirname, 'screenshot_login.png') });
    console.log("Login screenshot taken.");

    // Fill in login credentials (assuming there is an email and password field, and a submit button)
    // Adjust selectors to match actual application if necessary.
    console.log("Attempting login...");
    await page.type('input[type="email"]', 'test@example.com');
    await page.type('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Wait for navigation or network idle
    await page.waitForNavigation({ waitUntil: 'networkidle2' }).catch(() => {});
    await page.waitForTimeout(2000); // Give it some time to settle

    console.log("Taking dashboard screenshot...");
    await page.screenshot({ path: path.join(__dirname, 'screenshot_dashboard.png') });

    // Try interacting with new chat
    try {
      const buttons = await page.$$('button');
      for (const btn of buttons) {
        const text = await page.evaluate(el => el.innerText, btn);
        if (text && text.toLowerCase().includes('new chat')) {
          await btn.click();
          break;
        }
      }
      await page.waitForTimeout(1000);
    } catch(e) { console.error("New chat click failed", e.message); }

    // Take another screenshot for chat area
    await page.screenshot({ path: path.join(__dirname, 'screenshot_chat.png') });

    // Change viewport to mobile
    console.log("Switching to mobile view...");
    await page.setViewport({ width: 375, height: 812, isMobile: true });
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(__dirname, 'screenshot_mobile.png') });

  } catch (error) {
    console.error("Test execution failed:", error);
  } finally {
    await browser.close();
    console.log("Browser closed.");

    fs.writeFileSync(path.join(__dirname, 'browser_console.log'), logs.join('\n'));
    fs.writeFileSync(path.join(__dirname, 'network_requests.log'), networkRequests.join('\n'));
    console.log("Logs saved.");
  }
}

runTests();
