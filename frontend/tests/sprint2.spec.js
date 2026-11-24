import { test, expect } from '@playwright/test';

// These tests are designed to execute against the live environment.
// Note: To successfully run the Firebase Login test, Email/Password auth MUST be enabled
// in the Firebase Console (auth/operation-not-allowed is currently returned).

test.describe('Sprint 2: Final Verification Live Evidence', () => {

  test('Real Firebase Login & HttpOnly Cookie Visibility', async ({ page }) => {
    // 1. Login with real credentials
    await page.goto('/login');
    await page.fill('input[type="email"]', 'testuser99@example.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');

    // Wait for successful login (URL changes or UI updates)
    await expect(page).toHaveURL('/');

    // 2. Verify HttpOnly Refresh Cookie is NOT in localStorage/sessionStorage
    const localStorage = await page.evaluate(() => window.localStorage.getItem('refresh_token'));
    const sessionStorage = await page.evaluate(() => window.sessionStorage.getItem('refresh_token'));
    const jsCookies = await page.evaluate(() => document.cookie);
    
    expect(localStorage).toBeNull();
    expect(sessionStorage).toBeNull();
    expect(jsCookies).not.toContain('refresh_token'); // It's HttpOnly!

    // Verify Access Token is present in localStorage
    const accessToken = await page.evaluate(() => window.localStorage.getItem('access_token'));
    expect(accessToken).toBeTruthy();
  });

  test('Browser Restart Session Persistence', async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();

    // Login
    await page.goto('/login');
    await page.fill('input[type="email"]', 'testuser99@example.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');

    // Simulate browser restart by closing context and opening new one with SAME state (cookies)
    const storageState = await context.storageState();
    await context.close();

    const newContext = await browser.newContext({ storageState });
    const newPage = await newContext.newPage();
    
    // 3. Verify Silent Auth / No flash
    await newPage.goto('/');
    await expect(newPage.locator('text=Log out')).toBeVisible(); // User is still logged in
  });

  test('Multi-tab Logout Synchronization', async ({ browser }) => {
    const context = await browser.newContext();
    
    const tab1 = await context.newPage();
    const tab2 = await context.newPage();

    // Login in Tab 1
    await tab1.goto('/login');
    await tab1.fill('input[type="email"]', 'testuser99@example.com');
    await tab1.fill('input[type="password"]', 'Password123!');
    await tab1.click('button[type="submit"]');
    await expect(tab1).toHaveURL('/');

    // Load Tab 2, should be logged in
    await tab2.goto('/');
    await expect(tab2.locator('text=Log out')).toBeVisible();

    // Logout in Tab 1
    await tab1.click('text=Log out');
    await expect(tab1).toHaveURL('/login');

    // Tab 2 should automatically redirect to login via storage event
    await expect(tab2).toHaveURL('/login');
  });

  test('Refresh Queue: 10 concurrent requests -> 1 refresh', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'testuser99@example.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');

    // Erase the access_token to force all requests to fail with 401 and trigger a refresh
    await page.evaluate(() => window.localStorage.removeItem('access_token'));

    // Intercept network to count refresh requests
    let refreshCount = 0;
    page.on('request', request => {
      if (request.url().includes('/api/auth/refresh')) {
        refreshCount++;
      }
    });

    // Fire 10 concurrent protected API requests
    await page.evaluate(async () => {
      const promises = [];
      for(let i = 0; i < 10; i++) {
        promises.push(window.fetchWithAuth('/api/auth/me')); // Calls the custom interceptor
      }
      await Promise.all(promises);
    });

    // Verify only ONE refresh request was made despite 10 concurrent 401s
    expect(refreshCount).toBe(1);
  });

  test('Logout Clears React Query, LocalStorage, Auth State', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[type="email"]', 'testuser99@example.com');
    await page.fill('input[type="password"]', 'Password123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/');

    await page.click('text=Log out');

    // Local Storage
    const accessToken = await page.evaluate(() => window.localStorage.getItem('access_token'));
    expect(accessToken).toBeNull();

    // React Query Cache
    const cacheSize = await page.evaluate(() => window.queryClient.getQueryCache().findAll().length);
    expect(cacheSize).toBe(0);
  });

});
