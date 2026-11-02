const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const ARTIFACTS_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function run() {
  console.log('--- Starting Global Footer Layout & Viewport Verification ---');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1']
  });

  const page = await browser.newPage();

  // Test 1: Short Page - Garage Jobs at 1440x900
  console.log('\n1. Testing Short Page (Garage Jobs) at 1440x900...');
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  // Navigate to Garage Jobs
  const garageBtn = await page.$('button[aria-label="Garage Operations"]');
  if (garageBtn) await garageBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const shortGarageJobsState = await page.evaluate(() => {
    const footer = document.querySelector('footer');
    const main = document.querySelector('main');
    const footerRect = footer.getBoundingClientRect();
    const windowHeight = window.innerHeight;
    const footerComputed = window.getComputedStyle(footer);

    return {
      windowHeight,
      footerTop: Math.round(footerRect.top),
      footerBottom: Math.round(footerRect.bottom),
      footerPosition: footerComputed.position,
      distanceFromBottom: Math.round(windowHeight - footerRect.bottom),
      isAtViewportBottom: Math.abs(windowHeight - footerRect.bottom) <= 30,
      isFloatingMidway: footerRect.bottom < (windowHeight - 80),
      mainHeight: Math.round(main.getBoundingClientRect().height)
    };
  });
  console.log('Short Page (Garage Jobs 1440x900) Audit:', JSON.stringify(shortGarageJobsState, null, 2));

  const shotShort1440 = path.join(ARTIFACTS_DIR, 'footer_short_garage_jobs_1440.png');
  await page.screenshot({ path: shotShort1440, fullPage: false });
  console.log('Saved:', shotShort1440);

  // Test 2: Short Page - Garage Jobs at 1920x1080 (Tall viewport)
  console.log('\n2. Testing Short Page (Garage Jobs) at 1920x1080...');
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await new Promise(r => setTimeout(r, 400));

  const shortGarageJobs1080State = await page.evaluate(() => {
    const footer = document.querySelector('footer');
    const footerRect = footer.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    return {
      windowHeight,
      footerBottom: Math.round(footerRect.bottom),
      distanceFromBottom: Math.round(windowHeight - footerRect.bottom),
      isAtViewportBottom: Math.abs(windowHeight - footerRect.bottom) <= 30,
      isFloatingMidway: footerRect.bottom < (windowHeight - 80)
    };
  });
  console.log('Short Page (Garage Jobs 1920x1080) Audit:', JSON.stringify(shortGarageJobs1080State, null, 2));

  const shotShort1080 = path.join(ARTIFACTS_DIR, 'footer_short_garage_jobs_1080.png');
  await page.screenshot({ path: shotShort1080, fullPage: false });
  console.log('Saved:', shotShort1080);

  // Test 3: Short Page - Placeholder View (Reports) at 1440x900
  console.log('\n3. Testing Short Page (Reports Placeholder) at 1440x900...');
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('header button'));
    const reportsTab = tabs.find(t => t.textContent && t.textContent.includes('Reports'));
    if (reportsTab) reportsTab.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const placeholderState = await page.evaluate(() => {
    const footer = document.querySelector('footer');
    const footerRect = footer.getBoundingClientRect();
    const windowHeight = window.innerHeight;

    return {
      windowHeight,
      footerBottom: Math.round(footerRect.bottom),
      distanceFromBottom: Math.round(windowHeight - footerRect.bottom),
      isAtViewportBottom: Math.abs(windowHeight - footerRect.bottom) <= 30
    };
  });
  console.log('Reports Placeholder Footer Audit:', JSON.stringify(placeholderState, null, 2));

  const shotPlaceholder = path.join(ARTIFACTS_DIR, 'footer_short_placeholder_1440.png');
  await page.screenshot({ path: shotPlaceholder, fullPage: false });
  console.log('Saved:', shotPlaceholder);

  // Test 4: Long Page - All Vehicles (Lots of cards, scrollable)
  console.log('\n4. Testing Long Page (All Vehicles) at 1440x900...');
  const vehBtn = await page.$('button[aria-label="Vehicles"]');
  if (vehBtn) await vehBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const longVehiclesState = await page.evaluate(() => {
    const footer = document.querySelector('footer');
    const main = document.querySelector('main');
    const footerRect = footer.getBoundingClientRect();
    const mainRect = main.getBoundingClientRect();
    const footerComputed = window.getComputedStyle(footer);

    return {
      docHeight: document.body.scrollHeight,
      windowHeight: window.innerHeight,
      footerPosition: footerComputed.position,
      isFixed: footerComputed.position === 'fixed',
      footerTopRelativeContent: footerRect.top >= mainRect.top,
      footerAfterMain: footer.offsetTop >= main.offsetHeight
    };
  });
  console.log('Long Page (All Vehicles) Audit:', JSON.stringify(longVehiclesState, null, 2));

  const shotVehicles = path.join(ARTIFACTS_DIR, 'footer_long_vehicles_1440.png');
  await page.screenshot({ path: shotVehicles, fullPage: false });
  console.log('Saved:', shotVehicles);

  // Test 5: Long Page - Vehicle Detail
  console.log('\n5. Testing Long Page (Vehicle Detail)...');
  await page.evaluate(() => {
    const detailBtn = document.querySelector('button[title="View details"]');
    if (detailBtn) detailBtn.click();
  });
  await new Promise(r => setTimeout(r, 600));

  const vehDetailState = await page.evaluate(() => {
    const footer = document.querySelector('footer');
    const footerRect = footer.getBoundingClientRect();
    return {
      isFixed: window.getComputedStyle(footer).position === 'fixed',
      hasFooter: !!footer,
      footerText: footer.textContent.replace(/\s+/g, ' ').trim()
    };
  });
  console.log('Vehicle Detail Footer Audit:', JSON.stringify(vehDetailState, null, 2));

  const shotVehDetail = path.join(ARTIFACTS_DIR, 'footer_long_vehicle_detail_1440.png');
  await page.screenshot({ path: shotVehDetail, fullPage: false });
  console.log('Saved:', shotVehDetail);

  // Test 6: Dashboard at 1440x900
  console.log('\n6. Testing Dashboard at 1440x900...');
  const dashBtn = await page.$('button[aria-label="Dashboard"]');
  if (dashBtn) await dashBtn.click();
  await new Promise(r => setTimeout(r, 600));

  const shotDashboard = path.join(ARTIFACTS_DIR, 'footer_dashboard_1440.png');
  await page.screenshot({ path: shotDashboard, fullPage: false });
  console.log('Saved:', shotDashboard);

  // Test 7: Multi-viewport audit across required screen widths (Garage Jobs short page)
  console.log('\n7. Auditing Footer Bottom Placement across all required resolutions on short page...');
  // Navigate back to Garage Jobs to test bottom sticking across resolutions
  const gJobsBtn = await page.$('button[aria-label="Garage Operations"]');
  if (gJobsBtn) await gJobsBtn.click();
  await new Promise(r => setTimeout(r, 500));

  const viewports = [
    { name: '2560x1440', width: 2560, height: 1440 },
    { name: '1920x1080', width: 1920, height: 1080 },
    { name: '1600x900',  width: 1600, height: 900 },
    { name: '1440x900',  width: 1440, height: 900 },
    { name: '1366x768',  width: 1366, height: 768 },
    { name: '1280x800',  width: 1280, height: 800 },
    { name: 'tablet_768',width: 768,  height: 1024 },
    { name: 'mobile_375',width: 375,  height: 812 }
  ];

  for (const vp of viewports) {
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise(r => setTimeout(r, 300));

    const audit = await page.evaluate(() => {
      const footer = document.querySelector('footer');
      const footerRect = footer.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const distFromBottom = Math.round(windowHeight - footerRect.bottom);
      return {
        distFromBottom,
        isAtBottom: distFromBottom >= 0 && distFromBottom <= 32,
        isFixed: window.getComputedStyle(footer).position === 'fixed',
        hasOverflow: document.body.scrollWidth > window.innerWidth
      };
    });

    console.log(`Resolution ${vp.name.padEnd(11)}: isAtBottom = ${audit.isAtBottom} (dist: ${audit.distFromBottom}px), isFixed = ${audit.isFixed}, overflow = ${audit.hasOverflow}`);

    if (vp.name === 'tablet_768' || vp.name === 'mobile_375') {
      const vpShot = path.join(ARTIFACTS_DIR, `footer_${vp.name}.png`);
      await page.screenshot({ path: vpShot, fullPage: false });
      console.log('Saved:', vpShot);
    }
  }

  await browser.close();
  console.log('\n--- Footer Layout Verification Completed Successfully! ---');
}

run().catch(err => {
  console.error('Audit error:', err);
  process.exit(1);
});
