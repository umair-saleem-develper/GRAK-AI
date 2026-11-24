const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  // Capture all console logs
  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));

  // Capture network errors
  page.on('requestfailed', request => {
    console.log(`REQUEST FAILED: ${request.url()} - ${request.failure().errorText}`);
  });
  
  // Capture responses for /api/chat/stream
  page.on('response', async response => {
    if (response.url().includes('/api/chat/stream')) {
      console.log(`RESPONSE: ${response.url()} - ${response.status()}`);
      // Don't try to read body here if it's a stream, it might hang
    }
  });

  try {
    console.log("Navigating to login...");
    await page.goto('http://localhost:3000/login');
    
    // Fill login
    await page.fill('input[type="email"]', 'umair@test.com');
    await page.fill('input[type="password"]', 'umairtest123');
    await page.click('button[type="submit"]');
    console.log("Clicked login...");
    
    // Wait for dashboard
    await page.waitForURL('**/', { timeout: 10000 });
    console.log("On dashboard!");
    
    // Type hello
    await page.fill('textarea', 'Hello');
    
    // Click send
    console.log("Clicking send...");
    await page.click('button:has(svg.lucide-send)'); // The send button usually has a send icon
    
    // Wait a bit to observe
    await page.waitForTimeout(10000);
    
    console.log("Done waiting.");
  } catch (err) {
    console.error("Test error:", err);
  } finally {
    await browser.close();
  }
})();
