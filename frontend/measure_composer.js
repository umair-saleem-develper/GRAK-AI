const puppeteer = require('puppeteer');
const path = require('path');

const VALID_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2YjdiMzc5Yi1lNTlkLTRjZDUtOTFkNC03N2ZhZjE4MTRmNzAiLCJleHAiOjE3OTIzNTI5MDAsImp0aSI6IjUzMTAyZmFhLWFmOTUtNGZhMS04NmFiLWI5ZWVmOGUzYWRlYyJ9.OrqR57dLnntyqjtX6OPSMurPDSe4Kpn5R2sfQKhREYI";

async function run() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Set localStorage tokens before visiting dashboard
  await page.goto('http://localhost:3000/ping');
  await page.evaluate((tok) => {
    localStorage.setItem('access_token', tok);
    localStorage.setItem('has_logged_in', 'true');
  }, VALID_TOKEN);

  // Set viewport to 1920x1080
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://localhost:3000/', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  console.log('Dashboard loaded, current URL:', page.url());

  // 1. Measure empty state composer and widths at 1920x1080
  const metrics1920 = await page.evaluate(() => {
    const form = document.querySelector('form');
    const composerBox = form ? form.getBoundingClientRect() : null;
    const composerWrapper = form ? form.parentElement : null;
    const wrapperBox = composerWrapper ? composerWrapper.getBoundingClientRect() : null;
    const textarea = document.querySelector('textarea');
    const textareaBox = textarea ? textarea.getBoundingClientRect() : null;

    return {
      composerHeight: composerBox ? Math.round(composerBox.height) : null,
      composerWidth: composerBox ? Math.round(composerBox.width) : null,
      wrapperHeight: wrapperBox ? Math.round(wrapperBox.height) : null,
      textareaHeight: textareaBox ? Math.round(textareaBox.height) : null,
    };
  });
  console.log('--- METRICS 1920x1080 (EMPTY STATE) ---', JSON.stringify(metrics1920, null, 2));

  const shot1920Path = path.join(__dirname, 'screenshot_1920_after.png');
  await page.screenshot({ path: shot1920Path, fullPage: false });
  console.log('Saved 1920 screenshot to:', shot1920Path);

  // Test multi-line auto-grow (5 lines typed with Shift+Enter)
  await page.focus('textarea');
  for (let i = 1; i <= 5; i++) {
    await page.keyboard.type(`Line ${i} test content here`);
    if (i < 5) {
      await page.keyboard.down('Shift');
      await page.keyboard.press('Enter');
      await page.keyboard.up('Shift');
    }
  }
  await new Promise(r => setTimeout(r, 600));
  const metricsMultiline = await page.evaluate(() => {
    const form = document.querySelector('form');
    const textarea = document.querySelector('textarea');
    return {
      composerHeight: form ? Math.round(form.getBoundingClientRect().height) : null,
      textareaHeight: textarea ? Math.round(textarea.getBoundingClientRect().height) : null,
      textareaScrollHeight: textarea ? textarea.scrollHeight : null
    };
  });
  console.log('--- METRICS 1920x1080 (5 LINES TYPED) ---', JSON.stringify(metricsMultiline, null, 2));

  // Send message to transition into active chat and verify #scroller + message column
  console.log('Submitting message to enter chat state...');
  await page.keyboard.press('Enter');
  await new Promise(r => setTimeout(r, 6000));

  const metricsChat = await page.evaluate(() => {
    const scroller = document.getElementById('scroller');
    const form = document.querySelector('form');
    const composerBox = form ? form.getBoundingClientRect() : null;
    // Find the max-w-3xl message container inside scroller
    const msgContainer = scroller ? scroller.querySelector('.max-w-3xl') : null;
    const msgBox = msgContainer ? msgContainer.getBoundingClientRect() : null;
    const composerWrapper = form?.closest('.pointer-events-auto');
    const wrapperBox = composerWrapper ? composerWrapper.getBoundingClientRect() : null;

    // Check computed styles for chat-bg
    const computedChatBg = getComputedStyle(document.documentElement).getPropertyValue('--chat-bg').trim();
    const scrollerComputed = scroller ? getComputedStyle(scroller) : null;

    return {
      scrollerExists: !!scroller,
      scrollerClientHeight: scroller ? scroller.clientHeight : null,
      scrollerScrollHeight: scroller ? scroller.scrollHeight : null,
      composerWidth: composerBox ? Math.round(composerBox.width) : null,
      messageContainerWidth: msgBox ? Math.round(msgBox.width) : null,
      composerHeight: composerBox ? Math.round(composerBox.height) : null,
      totalBottomAreaHeight: wrapperBox ? Math.round(wrapperBox.height) : null,
      chatBgVariable: computedChatBg,
      scrollerPaddingBottom: scrollerComputed ? scrollerComputed.paddingBottom : null
    };
  });
  console.log('--- METRICS 1920x1080 (CHAT STATE) ---', JSON.stringify(metricsChat, null, 2));

  const shotChatPath = path.join(__dirname, 'screenshot_1920_chat_messages.png');
  await page.screenshot({ path: shotChatPath, fullPage: false });
  console.log('Saved 1920 chat screenshot to:', shotChatPath);

  // Switch to mobile viewport (375x812)
  console.log('Switching to mobile viewport 375x812...');
  await page.setViewport({ width: 375, height: 812 });
  await new Promise(r => setTimeout(r, 1000));
  const metrics375 = await page.evaluate(() => {
    const form = document.querySelector('form');
    const composerBox = form ? form.getBoundingClientRect() : null;
    const scroller = document.getElementById('scroller');
    const msgContainer = scroller ? scroller.querySelector('.max-w-3xl') : null;
    const msgBox = msgContainer ? msgContainer.getBoundingClientRect() : null;

    return {
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      bodyScrollWidth: document.body.scrollWidth,
      hasHorizontalOverflow: document.body.scrollWidth > window.innerWidth,
      composerWidth: composerBox ? Math.round(composerBox.width) : null,
      composerHeight: composerBox ? Math.round(composerBox.height) : null,
      messageContainerWidth: msgBox ? Math.round(msgBox.width) : null,
    };
  });
  console.log('--- METRICS 375x812 (MOBILE) ---', JSON.stringify(metrics375, null, 2));

  const shot375Path = path.join(__dirname, 'screenshot_375_after.png');
  await page.screenshot({ path: shot375Path, fullPage: false });
  console.log('Saved 375 mobile screenshot to:', shot375Path);

  await browser.close();
  console.log('All tests completed successfully!');
}

run().catch(err => {
  console.error('Puppeteer run error:', err);
  process.exit(1);
});
