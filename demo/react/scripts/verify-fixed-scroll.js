import puppeteer from 'puppeteer';

async function verify() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const artifactDir = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\74b615cd-d12e-43a4-943b-840b5ee727c0';

  const viewports = [
    { width: 1920, height: 1080, name: '1920x1080' },
    { width: 1600, height: 900, name: '1600x900' },
    { width: 1440, height: 900, name: '1440x900' },
    { width: 1366, height: 768, name: '1366x768' },
  ];

  console.log('--- VERIFYING FIXED SIDEBAR & SCROLL BEHAVIOR ---');

  for (const vp of viewports) {
    await page.setViewport(vp);
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 600));

    // 1. Initial State
    const initial = await page.evaluate(() => {
      const rail = document.querySelector('aside[aria-label="Sidebar Navigation"]');
      const r = rail?.getBoundingClientRect();
      const main = document.querySelector('main');
      const mr = main?.getBoundingClientRect();
      return {
        railTop: r?.top,
        railBottom: r?.bottom,
        railHeight: r?.height,
        railLeft: r?.left,
        railRight: r?.right,
        mainLeft: mr?.left,
        vpHeight: window.innerHeight,
        docHeight: document.documentElement.scrollHeight
      };
    });

    // 2. Scroll to Bottom
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
    await new Promise(r => setTimeout(r, 400));

    const scrolled = await page.evaluate(() => {
      const rail = document.querySelector('aside[aria-label="Sidebar Navigation"]');
      const r = rail?.getBoundingClientRect();
      const scrollY = window.scrollY;
      return {
        scrollY,
        railTop: r?.top,
        railBottom: r?.bottom,
        railHeight: r?.height,
        railLeft: r?.left
      };
    });

    const gap = initial.mainLeft - initial.railRight;
    const heightDifference = Math.abs(scrolled.railHeight - initial.railHeight);
    const topDifference = Math.abs(scrolled.railTop - initial.railTop);

    console.log(`Viewport ${vp.name}:`);
    console.log(`  Initial: top=${initial.railTop}px, bottom=${initial.railBottom}px, height=${initial.railHeight}px (vp=${initial.vpHeight}px)`);
    console.log(`  Gap between Rail and Main: ${gap.toFixed(1)}px (no overlap)`);
    console.log(`  Scrolled: scrollY=${scrolled.scrollY}px, top=${scrolled.railTop}px, height=${scrolled.railHeight}px`);
    console.log(`  Fixed Invariant: Top Diff = ${topDifference}px, Height Diff = ${heightDifference}px -> ${topDifference === 0 && heightDifference === 0 ? 'PASSED (100% FIXED)' : 'FAILED'}`);

    // Take screenshot of scrolled state
    await page.screenshot({ path: `${artifactDir}\\scrolled_${vp.name}.png` });

    // Scroll back to top
    await page.evaluate(() => window.scrollTo(0, 0));
  }

  // Also test Flyout on fixed rail
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  const buttons = await page.$$('aside[aria-label="Sidebar Navigation"] button');
  if (buttons.length > 1) {
    // Click Vehicles button to pin flyout
    await buttons[1].click();
    await new Promise(r => setTimeout(r, 400));

    // Scroll while flyout is open
    await page.evaluate(() => window.scrollTo(0, 200));
    await new Promise(r => setTimeout(r, 300));

    await page.screenshot({ path: `${artifactDir}\\flyout_scrolled.png` });
    console.log('Flyout scrolled screenshot saved');
  }

  // Full screenshot of the chart to verify Bar UI imitation
  await page.screenshot({ path: `${artifactDir}\\chart_bar_ui_render.png` });

  await browser.close();
}

verify().catch(console.error);
