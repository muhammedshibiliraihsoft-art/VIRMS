const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function run() {
  console.log('--- Starting Global Application Background & Layout Audit ---');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1']
  });

  const page = await browser.newPage();

  // Test 1: 2560x1440 Large Screen Audit (Verify App uses available width, not centered 1480px box)
  console.log('\n1. Testing 2560x1440 Ultrawide Display...');
  await page.setViewport({ width: 2560, height: 1440, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 800));

  const ultraWideState = await page.evaluate(() => {
    const main = document.querySelector('main');
    const body = document.body;
    const bodyStyle = window.getComputedStyle(body);
    const mainStyle = window.getComputedStyle(main);

    return {
      windowWidth: window.innerWidth,
      bodyScrollWidth: body.scrollWidth,
      mainWidth: main.offsetWidth,
      mainBorder: mainStyle.border,
      mainBorderRadius: mainStyle.borderRadius,
      mainBoxShadow: mainStyle.boxShadow,
      mainBgColor: mainStyle.backgroundColor,
      bodyBgColor: bodyStyle.backgroundColor,
      bodyBgImage: bodyStyle.backgroundImage.slice(0, 60) + '...',
      has1480Constraint: main.offsetWidth < 1600 && window.innerWidth >= 2560
    };
  });
  console.log('2560x1440 State:', JSON.stringify(ultraWideState, null, 2));

  const shot2560 = path.join(ARTIFACTS_DIR, 'global_bg_dashboard_2560.png');
  await page.screenshot({ path: shot2560, fullPage: false });
  console.log('Saved:', shot2560);

  // Test 2: 1920x1080 Standard Full HD Monitor
  console.log('\n2. Testing 1920x1080 Display...');
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await new Promise(r => setTimeout(r, 400));

  const fullHdState = await page.evaluate(() => {
    const main = document.querySelector('main');
    return {
      windowWidth: window.innerWidth,
      mainWidth: main.offsetWidth,
      has1480Constraint: main.offsetWidth <= 1480 && window.innerWidth >= 1920
    };
  });
  console.log('1920x1080 State:', JSON.stringify(fullHdState, null, 2));

  const shot1920 = path.join(ARTIFACTS_DIR, 'global_bg_dashboard_1920.png');
  await page.screenshot({ path: shot1920, fullPage: false });
  console.log('Saved:', shot1920);

  // Test 3: 1440x900 Dashboard
  console.log('\n3. Testing 1440x900 Laptop Display...');
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await new Promise(r => setTimeout(r, 400));

  const shot1440 = path.join(ARTIFACTS_DIR, 'global_bg_dashboard_1440.png');
  await page.screenshot({ path: shot1440, fullPage: false });
  console.log('Saved:', shot1440);

  // Test 4: All Vehicles Page (Full width multi-card grid)
  console.log('\n4. Testing All Vehicles full width grid...');
  const vehBtn = await page.$('button[aria-label="Vehicles"]');
  if (vehBtn) await vehBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const vehShot = path.join(ARTIFACTS_DIR, 'global_bg_all_vehicles_1920.png');
  await page.screenshot({ path: vehShot, fullPage: false });
  console.log('Saved:', vehShot);

  // Test 5: Vehicle Detail View
  console.log('\n5. Testing Vehicle Detail View without page card...');
  await page.evaluate(() => {
    const detailBtn = document.querySelector('button[title="View details"]');
    if (detailBtn) detailBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const vehDetailShot = path.join(ARTIFACTS_DIR, 'global_bg_vehicle_detail_1440.png');
  await page.screenshot({ path: vehDetailShot, fullPage: false });
  console.log('Saved:', vehDetailShot);

  // Test 6: Garage Jobs Work Queue
  console.log('\n6. Testing Garage Jobs Work Queue...');
  const garageBtn = await page.$('button[aria-label="Garage Operations"]');
  if (garageBtn) await garageBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const garageJobsShot = path.join(ARTIFACTS_DIR, 'global_bg_garage_jobs_1440.png');
  await page.screenshot({ path: garageJobsShot, fullPage: false });
  console.log('Saved:', garageJobsShot);

  // Test 7: Garage Job Detail (Orange dropdown card + tables)
  console.log('\n7. Testing Garage Job Detail...');
  await page.evaluate(() => {
    const btns = Array.from(document.querySelectorAll('button'));
    const detailsBtn = btns.find(b => b.textContent && b.textContent.includes('Details'));
    if (detailsBtn) detailsBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const jobDetailShot = path.join(ARTIFACTS_DIR, 'global_bg_garage_job_detail_1440.png');
  await page.screenshot({ path: jobDetailShot, fullPage: false });
  console.log('Saved:', jobDetailShot);

  // Test 8: Short Page Behavior (Reports / Pending view placeholder)
  console.log('\n8. Testing Short Page (Placeholder view) viewport coverage...');
  await page.evaluate(() => {
    // Select Inventory or Reports from top bar tabs
    const tabs = Array.from(document.querySelectorAll('header button'));
    const reportsTab = tabs.find(t => t.textContent && t.textContent.includes('Reports'));
    if (reportsTab) reportsTab.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const shortPageCheck = await page.evaluate(() => {
    const body = document.body;
    const html = document.documentElement;
    const bodyHeight = body.offsetHeight;
    const windowHeight = window.innerHeight;
    return {
      windowHeight,
      bodyHeight,
      fillsFullViewport: bodyHeight >= windowHeight,
      hasEmptyGapBelow: document.body.getBoundingClientRect().bottom < windowHeight
    };
  });
  console.log('Short Page Audit:', JSON.stringify(shortPageCheck, null, 2));

  const shortShot = path.join(ARTIFACTS_DIR, 'global_bg_short_page_1440.png');
  await page.screenshot({ path: shortShot, fullPage: false });
  console.log('Saved:', shortShot);

  // Test 9: Dark Theme Global Background
  console.log('\n9. Testing Dark Theme Global Background...');
  await page.evaluate(() => {
    const themeBtn = document.querySelector('button[title*="Switch to dark"]');
    if (themeBtn) themeBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const darkShot = path.join(ARTIFACTS_DIR, 'global_bg_dark_mode_1440.png');
  await page.screenshot({ path: darkShot, fullPage: false });
  console.log('Saved:', darkShot);

  // Test 10: Multi-viewport Overflow Audit
  console.log('\n10. Multi-viewport overflow audit across standard resolutions...');
  const viewports = [
    { name: '2560x1440', width: 2560, height: 1440 },
    { name: '1920x1080', width: 1920, height: 1080 },
    { name: '1600x900',  width: 1600, height: 900 },
    { name: '1440x900',  width: 1440, height: 900 },
    { name: '1366x768',  width: 1366, height: 768 },
    { name: '1280x800',  width: 1280, height: 800 },
    { name: '768x1024',  width: 768,  height: 1024 },
    { name: '375x812',   width: 375,  height: 812 }
  ];

  for (const vp of viewports) {
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise(r => setTimeout(r, 300));
    const overflow = await page.evaluate(() => ({
      scrollWidth: document.body.scrollWidth,
      innerWidth: window.innerWidth,
      hasOverflow: document.body.scrollWidth > window.innerWidth
    }));
    console.log(`Resolution ${vp.name.padEnd(10)}: hasOverflow = ${overflow.hasOverflow} (${overflow.scrollWidth}px vs ${overflow.innerWidth}px)`);
  }

  await browser.close();
  console.log('\n--- Verification Completed Successfully! ---');
}

run().catch(err => {
  console.error('Audit error:', err);
  process.exit(1);
});
