import puppeteer from 'puppeteer';

async function verifySharedShell() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const artifactDir = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\74b615cd-d12e-43a4-943b-840b5ee727c0';

  console.log('=== VERIFYING SHARED APPLICATION SHELL ===');

  // Test 1: Desktop Layout & TopBar Controls
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  // Check Brand
  const brandText = await page.evaluate(() => {
    return document.querySelector('header')?.innerText;
  });
  console.log('TopBar Header Content Detected:', brandText?.includes('VIRMS'));

  // Test 2: Garage Filter Selection
  console.log('Testing Garage Filter...');
  await page.evaluate(() => {
    // Open garage dropdown
    const btn = document.querySelector('button[aria-label^="Filter by branch"]');
    btn?.click();
  });
  await new Promise(r => setTimeout(r, 300));

  // Select West Garage
  const garageSelected = await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
    const westGarage = items.find(el => el.textContent.includes('West Garage'));
    if (westGarage) {
      westGarage.click();
      return true;
    }
    return false;
  });
  console.log('West Garage Selected:', garageSelected);
  await new Promise(r => setTimeout(r, 400));

  // Check Status Message appeared
  const statusMsgText = await page.evaluate(() => {
    const msg = document.querySelector('[role="status"], [role="alert"]');
    return msg ? msg.textContent : null;
  });
  console.log('Status Message on Garage Change:', statusMsgText);

  // Take screenshot with status message
  await page.screenshot({ path: `${artifactDir}\\shared_shell_garage_status.png` });

  // Test 3: Refresh Action
  console.log('Testing Refresh Control...');
  await page.evaluate(() => {
    const refreshBtn = document.querySelector('button[aria-label="Refresh data"]');
    refreshBtn?.click();
  });
  await new Promise(r => setTimeout(r, 200));

  // Check loading state
  const isSpinning = await page.evaluate(() => {
    const icon = document.querySelector('button[aria-label="Refresh data"] svg');
    return icon?.classList.contains('animate-spin');
  });
  console.log('Refresh Loading/Spinning State Active:', isSpinning);

  await new Promise(r => setTimeout(r, 800));
  const postRefreshMsg = await page.evaluate(() => {
    const msg = document.querySelector('[role="status"], [role="alert"]');
    return msg ? msg.textContent : null;
  });
  console.log('Status Message after Refresh:', postRefreshMsg);

  await page.screenshot({ path: `${artifactDir}\\shared_shell_refresh_done.png` });

  // Test 4: Mobile Viewport & Drawer
  console.log('Testing Mobile Drawer Trigger...');
  await page.setViewport({ width: 375, height: 812 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  await page.evaluate(() => {
    const menuBtn = document.querySelector('button[aria-label="Open mobile navigation menu"]');
    menuBtn?.click();
  });
  await new Promise(r => setTimeout(r, 400));

  await page.screenshot({ path: `${artifactDir}\\shared_shell_mobile_drawer.png` });
  console.log('Saved shared_shell_mobile_drawer.png');

  // Test 5: Multi-Viewport Responsive Check (0 Horizontal Overflow)
  console.log('Testing Multi-Viewport Responsiveness...');
  const viewports = [
    { width: 1920, height: 1080 },
    { width: 1600, height: 900 },
    { width: 1440, height: 900 },
    { width: 1366, height: 768 },
    { width: 1280, height: 800 },
    { width: 768, height: 1024 }, // Tablet
    { width: 375, height: 812 },  // Mobile
  ];

  for (const vp of viewports) {
    await page.setViewport(vp);
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 300));

    const overflow = await page.evaluate(() => {
      const docW = document.documentElement.scrollWidth;
      const innerW = window.innerWidth;
      return { docW, innerW, hasOverflow: docW > innerW };
    });

    console.log(`Viewport ${vp.width}x${vp.height}: scrollWidth=${overflow.docW}px, innerWidth=${overflow.innerW}px, Overflow=${overflow.hasOverflow}`);
  }

  await browser.close();
  console.log('=== VERIFICATION COMPLETED SUCCESSFULLY ===');
}

verifySharedShell().catch(console.error);
