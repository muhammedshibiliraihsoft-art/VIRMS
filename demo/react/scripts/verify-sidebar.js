import puppeteer from 'puppeteer';
import path from 'node:path';

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 1024, deviceScaleFactor: 2 });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('BROWSER ERROR:', err));

  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });

  // 1. Capture Default Narrow Rail
  const shot1 = path.resolve('C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/sidebar_rail_default.png');
  await page.screenshot({ path: shot1 });
  console.log('Saved 1:', shot1);

  // 2. Click Vehicles icon (second icon in rail) to trigger Pinned Flyout
  const buttons = await page.$$('nav button');
  if (buttons.length > 1) {
    await buttons[1].click(); // Vehicles
    await new Promise(r => setTimeout(r, 400));
    const shot2 = path.resolve('C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/sidebar_flyout_pinned.png');
    await page.screenshot({ path: shot2 });
    console.log('Saved 2 (Flyout):', shot2);
  }

  // 3. Click child item "Stock / Investor" inside flyout
  const flyoutButtons = await page.$$('div[role="region"] button');
  if (flyoutButtons.length > 2) {
    await flyoutButtons[2].click(); // "Stock / Investor"
    await new Promise(r => setTimeout(r, 400));
    const shot3 = path.resolve('C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/sidebar_pending_route.png');
    await page.screenshot({ path: shot3 });
    console.log('Saved 3 (Pending Route):', shot3);
  }

  // 4. Return to Dashboard
  const returnBtn = await page.$('button ::-p-text(Return to Dashboard Overview)');
  if (returnBtn) {
    await returnBtn.click();
    await new Promise(r => setTimeout(r, 400));
    console.log('Returned to dashboard successfully');
  }

  // 5. Test Mobile Viewport 390x844
  await page.setViewport({ width: 390, height: 844, deviceScaleFactor: 2 });
  await new Promise(r => setTimeout(r, 300));
  const mobileMenuBtn = await page.$('button[aria-label="Open navigation menu"]');
  if (mobileMenuBtn) {
    await mobileMenuBtn.click();
    await new Promise(r => setTimeout(r, 400));
    const shot4 = path.resolve('C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/sidebar_mobile_drawer.png');
    await page.screenshot({ path: shot4 });
    console.log('Saved 4 (Mobile Drawer):', shot4);
  }

  await browser.close();
}

main().catch(console.error);
