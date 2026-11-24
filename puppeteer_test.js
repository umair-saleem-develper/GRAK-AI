const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Set viewport for a good screenshot
  await page.setViewport({ width: 1280, height: 800 });

  // Listen to console
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.text()));

  // Listen to network
  const networkLogs = [];
  page.on('response', response => {
    const status = response.status();
    const url = response.url();
    if (url.includes('/api/auth/')) {
      networkLogs.push(`HTTP ${status} ${url}`);
      console.log(`[NETWORK] HTTP ${status} ${url}`);
    }
  });

  console.log('Navigating to login page...');
  await page.goto('http://localhost:3000/login');
  
  console.log('Waiting for email input...');
  await page.waitForSelector('input[type="email"]');
  
  console.log('Entering email...');
  await page.type('input[type="email"]', 'testuser@example.com');
  await page.click('button[type="submit"]');
  
  console.log('Waiting for OTP screen...');
  await page.waitForSelector('input[placeholder="Enter verification code"]');
  
  console.log('Entering OTP...');
  await page.type('input[placeholder="Enter verification code"]', '123456');
  await page.click('button[type="submit"]');
  
  console.log('Waiting for Dashboard to load...');
  await page.waitForNavigation();
  
  const token = await page.evaluate(() => localStorage.getItem('access_token'));
  if (token) {
    console.log('✅ Successfully logged in! Access token found in localStorage.');
  } else {
    console.log('❌ Failed to log in.');
  }

  // Artificial Expiration Test
  console.log('Modifying JWT to simulate upcoming expiration (expires in 10 seconds)...');
  await page.evaluate(() => {
    const t = localStorage.getItem('access_token');
    const parts = t.split('.');
    const payload = JSON.parse(atob(parts[1]));
    payload.exp = Math.floor(Date.now() / 1000) + 10; // Expires in 10 seconds
    parts[1] = btoa(JSON.stringify(payload));
    localStorage.setItem('access_token', parts.join('.'));
  });

  console.log('Triggering an authenticated API call via route reload...');
  await page.goto('http://localhost:3000/');
  
  console.log('Waiting 5 seconds to observe network activity...');
  await new Promise(r => setTimeout(r, 5000));

  // Taking screenshot
  const screenshotPath = 'C:/Users/us761/.gemini/antigravity/brain/b886d5fe-0b73-4b8f-b9f9-94f3e892aea4/proactive_refresh_proof.png';
  await page.screenshot({ path: screenshotPath });
  console.log('Screenshot saved to: ' + screenshotPath);

  console.log('\n--- NETWORK LOGS ---');
  networkLogs.forEach(log => console.log(log));
  
  const has401 = networkLogs.some(log => log.includes('HTTP 401'));
  const hasProactiveRefresh = networkLogs.some(log => log.includes('HTTP 200') && log.includes('/api/auth/refresh'));
  
  if (has401) {
    console.log('❌ Test Failed: A 401 error was observed in the network logs.');
  } else if (hasProactiveRefresh) {
    console.log('✅ Test Passed: Proactive refresh occurred successfully with zero 401 errors!');
  } else {
    console.log('⚠️ Test Inconclusive: No refresh or 401 occurred.');
  }

  await browser.close();
})();
