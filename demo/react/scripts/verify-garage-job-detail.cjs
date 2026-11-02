const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function run() {
  console.log('--- Starting Garage Job Detail & Updated Card Verification ---');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1']
  });

  const page = await browser.newPage();

  // Test 1: Vehicle Detail with updated left-aligned vertically-centered cards
  console.log('\n1. Verifying Vehicle Detail updated card styling...');
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 800));

  // Navigate to Vehicles
  const vehBtn = await page.$('button[aria-label="Vehicles"]');
  if (vehBtn) await vehBtn.click();
  await new Promise(r => setTimeout(r, 600));

  // Click "View details" on first vehicle to open Vehicle Detail
  await page.evaluate(() => {
    const detailBtn = document.querySelector('button[title="View details"]');
    if (detailBtn) detailBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  // Inspect the top summary cards in Vehicle Detail
  const vehicleCards = await page.evaluate(() => {
    // Top summary row has 5 cards (4 metrics + 1 vehicle image)
    const summaryGrid = document.querySelector('.grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-5');
    if (!summaryGrid) return { error: 'Summary grid not found' };

    const cards = Array.from(summaryGrid.children);
    return cards.slice(0, 4).map((c, i) => {
      const topLabelSpan = c.querySelector('.w-full span');
      const mainValDiv = c.querySelector('.my-auto');
      return {
        cardIndex: i,
        topLabel: topLabelSpan?.textContent?.trim() || '',
        topLabelAlign: topLabelSpan ? window.getComputedStyle(topLabelSpan.parentElement).textAlign : '',
        topLabelWeight: topLabelSpan ? window.getComputedStyle(topLabelSpan).fontWeight : '',
        mainValue: mainValDiv?.textContent?.trim() || '',
        mainValueAlign: mainValDiv ? window.getComputedStyle(mainValDiv).textAlign : '',
        mainValueJustify: mainValDiv ? window.getComputedStyle(mainValDiv).justifyContent : '',
        mainValueWeight: mainValDiv ? window.getComputedStyle(mainValDiv).fontWeight : '',
        cardHeight: c.offsetHeight
      };
    });
  });
  console.log('Vehicle Detail Card Audit:', JSON.stringify(vehicleCards, null, 2));

  const shot1 = path.join(ARTIFACTS_DIR, 'vehicle_detail_updated_cards_1440.png');
  await page.screenshot({ path: shot1, fullPage: false });
  console.log('Saved:', shot1);

  // Test 2: Navigate to Garage Operations > Garage Jobs
  console.log('\n2. Navigating to Garage Operations > Garage Jobs...');
  const garageBtn = await page.$('button[aria-label="Garage Operations"]');
  if (garageBtn) await garageBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const garageJobsListState = await page.evaluate(() => {
    const title = document.querySelector('h1')?.textContent || '';
    const tableRows = Array.from(document.querySelectorAll('tbody tr'));
    return {
      title,
      jobCount: tableRows.length,
      firstJob: tableRows[0]?.querySelector('td')?.textContent?.replace(/\s+/g, ' ').trim() || ''
    };
  });
  console.log('Garage Jobs List State:', JSON.stringify(garageJobsListState, null, 2));

  const shot2 = path.join(ARTIFACTS_DIR, 'garage_jobs_list_1440.png');
  await page.screenshot({ path: shot2, fullPage: false });
  console.log('Saved:', shot2);

  // Test 3: Click "Details" on JOB-1048 to open Garage Job Detail
  console.log('\n3. Opening Garage Job Detail for JOB-1048...');
  await page.evaluate(() => {
    // Find Details button for the first row or JOB-1048
    const btns = Array.from(document.querySelectorAll('button'));
    const detailsBtn = btns.find(b => b.textContent && b.textContent.includes('Details'));
    if (detailsBtn) detailsBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const jobDetailState = await page.evaluate(() => {
    const title = document.querySelector('h1')?.textContent || '';
    const orangeCard = document.querySelector('.dashboard-card-orange');
    const cards = Array.from(document.querySelectorAll('.grid > div'));
    const tables = Array.from(document.querySelectorAll('table'));
    return {
      title,
      orangeCardText: orangeCard?.textContent?.replace(/\s+/g, ' ').trim() || '',
      totalCards: cards.length,
      tables: tables.map(t => ({
        headers: Array.from(t.querySelectorAll('th')).map(th => th.textContent.trim()),
        rows: t.querySelectorAll('tbody tr').length
      }))
    };
  });
  console.log('Garage Job Detail State:', JSON.stringify(jobDetailState, null, 2));

  const shot3 = path.join(ARTIFACTS_DIR, 'garage_job_detail_collapsed_1440.png');
  await page.screenshot({ path: shot3, fullPage: false });
  console.log('Saved:', shot3);

  // Test 4: Open Orange Garage Selector Dropdown
  console.log('\n4. Opening Orange Garage Selector Dropdown...');
  await page.evaluate(() => {
    const orangeCard = document.querySelector('.dashboard-card-orange');
    if (orangeCard) orangeCard.click();
  });
  await new Promise(r => setTimeout(r, 400));

  const dropdownState = await page.evaluate(() => {
    const popover = document.querySelector('[data-testid="garage-dropdown-menu"]');
    if (!popover) return { open: false };
    const items = Array.from(popover.querySelectorAll('button'));
    return {
      open: true,
      branchCount: items.length,
      branches: items.map(b => b.textContent.replace(/\s+/g, ' ').trim())
    };
  });
  console.log('Garage Dropdown State:', JSON.stringify(dropdownState, null, 2));

  const shot4 = path.join(ARTIFACTS_DIR, 'garage_job_detail_expanded_dropdown_1440.png');
  await page.screenshot({ path: shot4, fullPage: false });
  console.log('Saved:', shot4);

  // Switch Garage to West Garage
  console.log('\n5. Switching garage to West Garage...');
  await page.evaluate(() => {
    const popover = document.querySelector('[data-testid="garage-dropdown-menu"]');
    if (popover) {
      const westBtn = Array.from(popover.querySelectorAll('button')).find(b => b.textContent.includes('West Garage'));
      if (westBtn) westBtn.click();
    }
  });
  await new Promise(r => setTimeout(r, 500));

  const postSwitchState = await page.evaluate(() => {
    const orangeCard = document.querySelector('.dashboard-card-orange');
    return {
      orangeCardText: orangeCard?.textContent?.replace(/\s+/g, ' ').trim() || ''
    };
  });
  console.log('Post Switch State:', JSON.stringify(postSwitchState, null, 2));

  // Multi-viewport responsiveness
  console.log('\n6. Checking multi-viewport responsiveness...');
  const viewports = [
    { name: '1280x800', width: 1280, height: 800 },
    { name: 'tablet_768', width: 768, height: 1024 },
    { name: 'mobile_375', width: 375, height: 812 }
  ];

  for (const vp of viewports) {
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise(r => setTimeout(r, 400));

    const overflow = await page.evaluate(() => ({
      bodyScrollWidth: document.body.scrollWidth,
      windowInnerWidth: window.innerWidth,
      hasHorizontalOverflow: document.body.scrollWidth > window.innerWidth
    }));
    console.log(`Viewport ${vp.name}: overflow =`, overflow.hasHorizontalOverflow, `(${overflow.bodyScrollWidth} vs ${overflow.windowInnerWidth})`);

    const vpShot = path.join(ARTIFACTS_DIR, `garage_job_detail_${vp.name}.png`);
    await page.screenshot({ path: vpShot, fullPage: false });
    console.log('Saved:', vpShot);
  }

  await browser.close();
  console.log('\n--- Verification Completed Successfully! ---');
}

run().catch(err => {
  console.error('Test error:', err);
  process.exit(1);
});
