import puppeteer from 'puppeteer';
import path from 'path';

const ARTIFACT_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function verifyCompactVehicles() {
  console.log('🚀 Starting Puppeteer Verification for Compact Vehicles & Navigation Hierarchy...');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1'],
  });

  const page = await browser.newPage();

  // Test 1: Navigation Hierarchy & Flyout at 1440x900
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });

  // Hover or click Vehicles rail icon
  const vehiclesButton = await page.$('button[aria-label="Vehicles"]');
  if (!vehiclesButton) {
    throw new Error('Vehicles button not found in sidebar rail');
  }

  // Hover to trigger flyout
  await vehiclesButton.hover();
  await new Promise((r) => setTimeout(r, 400));

  // Check flyout content
  const flyoutItems = await page.evaluate(() => {
    const flyout = document.querySelector('[role="region"][aria-label="Vehicles submenu"]');
    if (!flyout) return null;
    const buttons = Array.from(flyout.querySelectorAll('div.flex.flex-col.gap-1 button'));
    return buttons.map((b) => b.textContent?.trim() || '');
  });

  console.log('Flyout items:', flyoutItems);
  const hasAllVehiclesInFlyout = flyoutItems?.some((t) => t.includes('All Vehicles'));
  const hasStockInvestor = flyoutItems?.some((t) => t.includes('Stock / Investor'));
  const hasCustomerVehicles = flyoutItems?.some((t) => t.includes('Customer Vehicles'));

  console.log('Flyout checks:');
  console.log(' - "All Vehicles" excluded from nested items:', !hasAllVehiclesInFlyout);
  console.log(' - "Stock / Investor" present:', hasStockInvestor);
  console.log(' - "Customer Vehicles" present:', hasCustomerVehicles);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'verify_vehicles_flyout_1440.png'),
    fullPage: false,
  });

  // Click Vehicles rail icon -> Should open All Vehicles
  await vehiclesButton.click();
  await new Promise((r) => setTimeout(r, 400));

  // Verify All Vehicles page title and card count
  const allVehiclesTitle = await page.$eval('h1', (el) => el.textContent?.trim());
  console.log('Page Title after clicking Vehicles rail icon:', allVehiclesTitle);

  // Check card metrics at 1440x900
  const cardMetrics1440 = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.grid > div'));
    if (cards.length === 0) return null;
    const first = cards[0].getBoundingClientRect();
    const rows = new Set(cards.map((c) => Math.round(c.getBoundingClientRect().top)));
    // calculate cards in first row
    const firstRowCards = cards.filter(
      (c) => Math.abs(c.getBoundingClientRect().top - first.top) < 10
    );
    return {
      cardCount: cards.length,
      cardsInFirstRow: firstRowCards.length,
      firstCardWidth: Math.round(first.width),
      firstCardHeight: Math.round(first.height),
      approxFootprint: Math.round(first.width * first.height),
    };
  });
  console.log('1440x900 Cards per row & dimensions:', cardMetrics1440);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'compact_vehicles_1440x900.png'),
    fullPage: false,
  });

  // Test 2: Test 1920x1080 (Large Desktop: target 4-5 cards per row)
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await new Promise((r) => setTimeout(r, 300));
  const cardMetrics1920 = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.grid > div'));
    if (cards.length === 0) return null;
    const first = cards[0].getBoundingClientRect();
    const firstRowCards = cards.filter(
      (c) => Math.abs(c.getBoundingClientRect().top - first.top) < 10
    );
    return {
      cardCount: cards.length,
      cardsInFirstRow: firstRowCards.length,
      firstCardWidth: Math.round(first.width),
      firstCardHeight: Math.round(first.height),
    };
  });
  console.log('1920x1080 Cards per row:', cardMetrics1920);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'compact_vehicles_1920x1080.png'),
    fullPage: false,
  });

  // Test 3: Navigate to Stock / Investor view via sidebar flyout or right panel
  console.log('Navigating to Stock / Investor view...');
  // Click Stock / Investor button in right panel or flyout
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const stockBtn = buttons.find((b) => b.textContent?.includes('Stock / Investor'));
    if (stockBtn) stockBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  const stockTitle = await page.$eval('h1', (el) => el.textContent?.trim());
  const stockVehicleTypes = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.grid > div'));
    return cards.map((c) => c.querySelector('span')?.textContent?.trim());
  });
  console.log('Stock / Investor View Title:', stockTitle);
  console.log('Displayed vehicle types in Stock view:', stockVehicleTypes);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'compact_vehicles_stock_view.png'),
    fullPage: false,
  });

  // Test 4: Navigate to Customer Vehicles view
  console.log('Navigating to Customer Vehicles view...');
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const custBtn = buttons.find((b) => b.textContent?.includes('Customer Vehicles'));
    if (custBtn) custBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  const customerTitle = await page.$eval('h1', (el) => el.textContent?.trim());
  const customerCount = await page.evaluate(() => {
    return document.querySelectorAll('.grid > div').length;
  });
  console.log('Customer Vehicles View Title:', customerTitle);
  console.log('Displayed vehicle count in Customer view:', customerCount);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'compact_vehicles_customer_view.png'),
    fullPage: false,
  });

  // Test 5: Responsive viewports & 0 horizontal overflow check
  const viewports = [
    { name: '1600x900', width: 1600, height: 900 },
    { name: '1366x768', width: 1366, height: 768 },
    { name: '1280x800', width: 1280, height: 800 },
    { name: 'tablet_768', width: 768, height: 1024 },
    { name: 'mobile_375', width: 375, height: 812 },
  ];

  // Go back to All Vehicles for responsive checks
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const allBtn = buttons.find((b) => b.textContent?.includes('All Vehicles'));
    if (allBtn) allBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  for (const vp of viewports) {
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise((r) => setTimeout(r, 200));

    const overflowCheck = await page.evaluate(() => {
      const docWidth = document.documentElement.scrollWidth;
      const winWidth = window.innerWidth;
      const cards = Array.from(document.querySelectorAll('.grid > div'));
      const first = cards[0]?.getBoundingClientRect();
      const firstRowCards = cards.filter(
        (c) => Math.abs(c.getBoundingClientRect().top - (first ? first.top : 0)) < 10
      );
      return {
        hasOverflow: docWidth > winWidth,
        docWidth,
        winWidth,
        cardsInRow: firstRowCards.length,
      };
    });

    console.log(`Viewport ${vp.name}: overflow=${overflowCheck.hasOverflow}, cardsInRow=${overflowCheck.cardsInRow}`);
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, `compact_vehicles_${vp.name}.png`),
      fullPage: false,
    });
  }

  await browser.close();
  console.log('🎉 Puppeteer Verification Complete!');
}

verifyCompactVehicles().catch((err) => {
  console.error('Error during verification:', err);
  process.exit(1);
});
