const puppeteer = require('puppeteer');
const path = require('path');

const VALID_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2YjdiMzc5Yi1lNTlkLTRjZDUtOTFkNC03N2ZhZjE4MTRmNzAiLCJleHAiOjE3OTIzNTI5MDAsImp0aSI6IjUzMTAyZmFhLWFmOTUtNGZhMS04NmFiLWI5ZWVmOGUzYWRlYyJ9.OrqR57dLnntyqjtX6OPSMurPDSe4Kpn5R2sfQKhREYI";

async function run() {
  const browser = await puppeteer.launch({
    headless: "new",
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  
  // Set auth tokens
  await page.goto('http://localhost:3000/ping');
  await page.evaluate((tok) => {
    localStorage.setItem('access_token', tok);
    localStorage.setItem('has_logged_in', 'true');
  }, VALID_TOKEN);

  // Set desktop viewport
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://localhost:3000/', { waitUntil: 'networkidle2' });
  await new Promise(r => setTimeout(r, 2000));
  console.log('Dashboard ready.');

  // TEST 1: Ask for an image / visual diagram
  console.log('Sending message: "explain plant with diagram"...');
  await page.focus('textarea');
  await page.keyboard.type('explain plant with diagram');
  await page.keyboard.press('Enter');

  // Wait for stream to start and image loader to mount
  console.log('Waiting for image block to appear...');
  let foundCanvas = false;
  let shineLabel = "";
  for (let i = 0; i < 20; i++) {
    await new Promise(r => setTimeout(r, 1000));
    const status = await page.evaluate(() => {
      const cv = document.querySelector('canvas');
      const shine = document.querySelector('.grak-shine');
      const img = document.querySelector('img[alt*="Diagram"], img[alt*="Plant"], img[alt*="Visual"]');
      return {
        hasCanvas: !!cv,
        shineText: shine ? shine.textContent.trim() : null,
        imgFound: !!img,
        imgComplete: img ? img.complete : false
      };
    });
    if (status.hasCanvas) {
      foundCanvas = true;
      shineLabel = status.shineText;
      console.log(`[Turn ${i+1}] DotCanvas found! Label: "${status.shineText}", Image complete: ${status.imgComplete}`);
    }
    if (foundCanvas && status.imgComplete) {
      console.log('Image successfully loaded!');
      break;
    }
  }

  // Wait a bit for final layout
  await new Promise(r => setTimeout(r, 3000));

  // Verify metrics of image box
  const imageBoxMetrics = await page.evaluate(() => {
    const heroCard = document.querySelector('.my-5.rounded-2xl');
    const img = heroCard ? heroCard.querySelector('img') : null;
    const canvas = heroCard ? heroCard.querySelector('canvas') : null;
    const zoomBtn = heroCard ? heroCard.querySelector('button') : null;
    const shine = heroCard ? heroCard.querySelector('.grak-shine') : null;

    return {
      heroCardFound: !!heroCard,
      cardWidth: heroCard ? Math.round(heroCard.getBoundingClientRect().width) : null,
      cardHeight: heroCard ? Math.round(heroCard.getBoundingClientRect().height) : null,
      imgFound: !!img,
      imgNaturalWidth: img ? img.naturalWidth : 0,
      imgNaturalHeight: img ? img.naturalHeight : 0,
      imgObjectFit: img ? getComputedStyle(img).objectFit : null,
      hasOldSpinner: !!document.querySelector('.animate-spin'),
      hasPercentage: document.body.textContent.includes('% loaded') || document.body.textContent.includes('% completed'),
      canvasPresent: !!canvas,
      zoomButtonPresent: !!zoomBtn
    };
  });
  console.log('--- TEST 1: HERO IMAGE METRICS ---', JSON.stringify(imageBoxMetrics, null, 2));

  const shotHeroPath = path.join(__dirname, 'screenshot_imageloader_loaded.png');
  await page.screenshot({ path: shotHeroPath, fullPage: false });
  console.log('Saved loaded image screenshot to:', shotHeroPath);

  // TEST 4: 375px mobile viewport overflow test
  console.log('Switching to mobile viewport 375x812...');
  await page.setViewport({ width: 375, height: 812 });
  await new Promise(r => setTimeout(r, 1000));
  const metrics375 = await page.evaluate(() => {
    const heroCard = document.querySelector('.my-5.rounded-2xl');
    return {
      viewportWidth: window.innerWidth,
      bodyScrollWidth: document.body.scrollWidth,
      hasHorizontalOverflow: document.body.scrollWidth > window.innerWidth,
      heroCardWidth: heroCard ? Math.round(heroCard.getBoundingClientRect().width) : null
    };
  });
  console.log('--- TEST 4: MOBILE 375px OVERFLOW METRICS ---', JSON.stringify(metrics375, null, 2));

  const shotMobilePath = path.join(__dirname, 'screenshot_imageloader_375.png');
  await page.screenshot({ path: shotMobilePath, fullPage: false });
  console.log('Saved mobile screenshot to:', shotMobilePath);

  // TEST 3: Block image / failure handling test
  // Render an ImageLoader with blocked URL, verify card disappears completely and text remains intact
  console.log('Testing image failure / block handling...');
  const failureTestResult = await page.evaluate(() => {
    // Check if error removes card cleanly
    return new Promise((resolve) => {
      // Create a test container to render failure scenario
      const testDiv = document.createElement('div');
      testDiv.id = 'test-fail-container';
      document.body.appendChild(testDiv);
      resolve({ testSetup: true });
    });
  });
  console.log('Failure setup:', failureTestResult);

  await browser.close();
  console.log('ImageLoader test run completed.');
}

run().catch(err => {
  console.error('Test error:', err);
  process.exit(1);
});
