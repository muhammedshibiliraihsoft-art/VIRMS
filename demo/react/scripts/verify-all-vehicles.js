import puppeteer from 'puppeteer';

async function verifyAllVehicles() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const artifactDir = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\74b615cd-d12e-43a4-943b-840b5ee727c0';

  console.log('=== VERIFYING ALL VEHICLES PAGE (IMAGE 1 COMPOSITION) ===');

  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  // 1. Navigate to All Vehicles via TopBar tab
  console.log('1. Navigating to Vehicles...');
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('nav[aria-label="Quick section navigation"] button'));
    const vehiclesTab = tabs.find(t => t.textContent.includes('Vehicles'));
    vehiclesTab?.click();
  });
  await new Promise(r => setTimeout(r, 600));

  // 2. Count rendered vehicle cards
  const cardsInfo = await page.evaluate(() => {
    const heading = document.querySelector('h1')?.textContent;
    const cards = Array.from(document.querySelectorAll('.grid > div.group'));
    const numbers = cards.map(c => c.querySelector('h2')?.textContent);
    const rightPanelTitle = document.querySelector('aside h2')?.textContent;
    const totalCount = document.querySelector('aside .text-xl')?.textContent;
    return {
      heading,
      cardCount: cards.length,
      numbers,
      rightPanelTitle,
      totalCount
    };
  });
  console.log('Page Title:', cardsInfo.heading);
  console.log('Vehicle Card Count:', cardsInfo.cardCount);
  console.log('Vehicle Registrations:', cardsInfo.numbers);
  console.log('Right Panel:', cardsInfo.rightPanelTitle, 'Total registered:', cardsInfo.totalCount);

  // Take screenshot of All Vehicles page default state
  await page.screenshot({ path: `${artifactDir}\\all_vehicles_default_1440.png` });
  console.log('Saved all_vehicles_default_1440.png');

  // 3. Test Search
  console.log('2. Testing Search: "Rubicon"...');
  await page.type('input[placeholder^="Search registration"]', 'Rubicon');
  await new Promise(r => setTimeout(r, 300));

  const searchResults = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.grid > div.group'));
    return cards.map(c => c.querySelector('h2')?.textContent);
  });
  console.log('Search Results for "Rubicon":', searchResults);
  await page.screenshot({ path: `${artifactDir}\\all_vehicles_search_rubicon.png` });

  // Clear search
  await page.evaluate(() => {
    const input = document.querySelector('input[placeholder^="Search registration"]');
    if (input) {
      input.value = '';
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });
  await new Promise(r => setTimeout(r, 300));

  // 4. Test Category Filter (Stock / Investor)
  console.log('3. Testing Category Filter: "Stock"...');
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const stockBtn = btns.find(b => b.textContent.trim() === 'Stock');
    stockBtn?.click();
  });
  await new Promise(r => setTimeout(r, 300));

  const stockCount = await page.evaluate(() => {
    return document.querySelectorAll('.grid > div.group').length;
  });
  console.log('Stock / Investor Card Count:', stockCount);
  await page.screenshot({ path: `${artifactDir}\\all_vehicles_stock_filter.png` });

  // Reset category filter to All
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const allBtn = btns.find(b => b.textContent.trim() === 'All');
    allBtn?.click();
  });
  await new Promise(r => setTimeout(r, 300));

  // 5. Test Shared Garage Filter Integration
  console.log('4. Testing Shared Garage Filter Integration: Central Garage...');
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label^="Filter by branch"]');
    btn?.click();
  });
  await new Promise(r => setTimeout(r, 300));

  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
    const central = items.find(el => el.textContent.includes('Central Garage'));
    central?.click();
  });
  await new Promise(r => setTimeout(r, 400));

  const centralCount = await page.evaluate(() => {
    return {
      cardCount: document.querySelectorAll('.grid > div.group').length,
      panelCount: document.querySelector('aside .text-xl')?.textContent
    };
  });
  console.log('Central Garage Filtered Cards:', centralCount.cardCount, 'Panel Count:', centralCount.panelCount);
  await page.screenshot({ path: `${artifactDir}\\all_vehicles_central_garage.png` });

  // Reset garage filter to All Garages
  await page.evaluate(() => {
    const btn = document.querySelector('button[aria-label^="Filter by branch"]');
    btn?.click();
  });
  await new Promise(r => setTimeout(r, 300));
  await page.evaluate(() => {
    const items = Array.from(document.querySelectorAll('[role="menuitem"]'));
    const all = items.find(el => el.textContent.includes('All Garages'));
    all?.click();
  });
  await new Promise(r => setTimeout(r, 400));

  // 6. Test Responsive Viewports for All Vehicles Page
  console.log('5. Testing Multi-Viewport Responsiveness...');
  const viewports = [
    { width: 1920, height: 1080, name: '1920x1080' },
    { width: 1600, height: 900, name: '1600x900' },
    { width: 1440, height: 900, name: '1440x900' },
    { width: 1366, height: 768, name: '1366x768' },
    { width: 1280, height: 800, name: '1280x800' },
    { width: 768, height: 1024, name: 'tablet_768' },
    { width: 375, height: 812, name: 'mobile_375' }
  ];

  for (const vp of viewports) {
    await page.setViewport(vp);
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 300));

    // Navigate to Vehicles
    await page.evaluate(() => {
      const tabs = Array.from(document.querySelectorAll('nav[aria-label="Quick section navigation"] button'));
      const vehiclesTab = tabs.find(t => t.textContent.includes('Vehicles'));
      if (vehiclesTab) vehiclesTab.click();
    });
    await new Promise(r => setTimeout(r, 300));

    const overflow = await page.evaluate(() => {
      return {
        docW: document.documentElement.scrollWidth,
        innerW: window.innerWidth,
        hasOverflow: document.documentElement.scrollWidth > window.innerWidth
      };
    });

    console.log(`Viewport ${vp.name} (${vp.width}x${vp.height}): scrollWidth=${overflow.docW}px, innerWidth=${overflow.innerW}px, Overflow=${overflow.hasOverflow}`);
    await page.screenshot({ path: `${artifactDir}\\all_vehicles_${vp.name}.png` });
  }

  await browser.close();
  console.log('=== ALL VEHICLES VERIFICATION COMPLETE ===');
}

verifyAllVehicles().catch(console.error);
