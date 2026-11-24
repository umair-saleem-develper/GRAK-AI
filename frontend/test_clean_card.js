const puppeteer = require('puppeteer');
const path = require('path');

const ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2YjdiMzc5Yi1lNTlkLTRjZDUtOTFkNC03N2ZhZjE4MTRmNzAiLCJleHAiOjE3OTI5NTgzOTAsImp0aSI6ImQwZjhhY2NiLTRmYTktNDFhOS05MDcxLTMzZTgzNGE4OWFkZiJ9.XNZZ_8TfavrzT9hfOaT9DFvSNV-mToAT2rR1XLwxKd8";
const REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2YjdiMzc5Yi1lNTlkLTRjZDUtOTFkNC03N2ZhZjE4MTRmNzAiLCJleHAiOjE3OTI5NTgzOTAsInR5cGUiOiJyZWZyZXNoIiwianRpIjoiODk4OGIyYzItZmRmNy00Y2YyLWJjZWMtMmNhY2M4YmJmODUwIn0.REcipJc66dmYihuk6jtRQemac5kFU-f8YcIdDbJrBBg";

async function run() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Set auth tokens in localStorage
  await page.goto('http://localhost:3000/ping');
  await page.evaluate((acc, ref) => {
    localStorage.setItem('access_token', acc);
    localStorage.setItem('refresh_token', ref);
    localStorage.setItem('has_logged_in', 'true');
  }, ACCESS_TOKEN, REFRESH_TOKEN);

  // Set viewport to 1920x1080
  await page.setViewport({ width: 1920, height: 1080 });

  // Load Generated Image conversation
  console.log('Loading GeneratedImage conversation: f82fa174-2cac-4269-b48d-bd6caca275c8...');
  await page.goto('http://localhost:3000/?c=f82fa174-2cac-4269-b48d-bd6caca275c8', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 3500));

  const cardAudit = await page.evaluate(() => {
    const card = document.querySelector('.my-5.rounded-2xl');
    const allText = card ? card.innerText.trim() : "";
    const hasHeaderBar = !!document.querySelector('.bg-\\[\\#161622\\]');
    const hasFooterPrompt = !!Array.from(document.querySelectorAll('span')).find(s => s.textContent.includes('Prompt: "'));
    const hasEngineLabel = !!document.body.innerText.includes('FLUX.1 Engine') || !!document.body.innerText.includes('Pollinations');
    const hasSparklesBadge = !!document.body.innerText.includes('AI Generated Visual');
    const zoomButton = card ? card.querySelector('button[title="Zoom image"]') : null;
    const img = card ? card.querySelector('img') : null;

    return {
      cardExists: !!card,
      visibleTextInsideCard: allText,
      hasHeaderBar,
      hasFooterPrompt,
      hasEngineLabel,
      hasSparklesBadge,
      hasZoomButton: !!zoomButton,
      imgFound: !!img,
      imgObjectFit: img ? getComputedStyle(img).objectFit : null,
      imgAlt: img ? img.alt : null
    };
  });
  console.log('--- AUDIT: GeneratedImageCard (CLEAN CARD CHECK) ---', JSON.stringify(cardAudit, null, 2));

  const shotCleanCard = path.join(__dirname, 'evidence_clean_card_1920.png');
  await page.screenshot({ path: shotCleanCard, fullPage: false });
  console.log('Saved clean card screenshot to:', shotCleanCard);

  // Test zoom modal
  console.log('Testing Zoom button and modal controls...');
  await page.evaluate(() => {
    const zoomBtn = document.querySelector('button[title="Zoom image"]');
    if (zoomBtn) zoomBtn.click();
  });
  await new Promise(r => setTimeout(r, 1000));

  const modalControls = await page.evaluate(() => {
    const modal = document.querySelector('.fixed.inset-0.z-50');
    const saveBtn = modal ? modal.querySelector('button[title="Download full resolution image"]') : null;
    const regenBtn = modal ? modal.querySelector('button[title="Regenerate variation"]') : null;
    const closeBtn = modal ? modal.querySelector('button[title="Close"]') : null;

    return {
      modalOpen: !!modal,
      hasSaveButtonInModal: !!saveBtn,
      hasRegenerateButtonInModal: !!regenBtn,
      hasCloseButtonInModal: !!closeBtn
    };
  });
  console.log('--- AUDIT: Zoom Modal Controls ---', JSON.stringify(modalControls, null, 2));

  const shotModal = path.join(__dirname, 'evidence_zoom_modal.png');
  await page.screenshot({ path: shotModal, fullPage: false });
  console.log('Saved zoom modal screenshot to:', shotModal);

  // Close modal
  await page.evaluate(() => {
    const close = document.querySelector('button[title="Close"]');
    if (close) close.click();
  });
  await new Promise(r => setTimeout(r, 500));

  // Test mobile 375px
  console.log('Switching to mobile viewport 375x812...');
  await page.setViewport({ width: 375, height: 812 });
  await new Promise(r => setTimeout(r, 1000));

  const mobileCheck = await page.evaluate(() => {
    const card = document.querySelector('.my-5.rounded-2xl');
    return {
      viewportWidth: window.innerWidth,
      bodyScrollWidth: document.body.scrollWidth,
      hasHorizontalOverflow: document.body.scrollWidth > window.innerWidth,
      cardWidth: card ? Math.round(card.getBoundingClientRect().width) : null
    };
  });
  console.log('--- AUDIT: Mobile 375px Check ---', JSON.stringify(mobileCheck, null, 2));

  const shotMobile = path.join(__dirname, 'evidence_clean_card_375.png');
  await page.screenshot({ path: shotMobile, fullPage: false });
  console.log('Saved mobile screenshot to:', shotMobile);

  await browser.close();
  console.log('Audit completed successfully!');
}

run().catch(err => {
  console.error('Audit error:', err);
  process.exit(1);
});
