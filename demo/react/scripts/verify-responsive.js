import puppeteer from 'puppeteer';
import path from 'node:path';

const viewports = [
  { name: '1920x1080', width: 1920, height: 1080 },
  { name: '1600x900',  width: 1600, height: 900 },
  { name: '1440x900',  width: 1440, height: 900 },
  { name: '1366x768',  width: 1366, height: 768 },
  { name: '1280x800',  width: 1280, height: 800 },
];

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();

  // Load once
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded', timeout: 10000 });
  await new Promise(r => setTimeout(r, 600));

  for (const vp of viewports) {
    // 100% zoom (deviceScaleFactor = 1)
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise(r => setTimeout(r, 400));

    // Check horizontal overflow
    const overflow = await page.evaluate(() => {
      const docWidth = document.documentElement.scrollWidth;
      const winWidth = window.innerWidth;
      const bodyWidth = document.body.scrollWidth;
      return {
        hasHorizontalScroll: docWidth > winWidth || bodyWidth > winWidth,
        scrollWidth: docWidth,
        innerWidth: winWidth,
        bodyWidth: bodyWidth,
      };
    });

    const shotPath = path.resolve(`C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/vp_${vp.name}.png`);
    await page.screenshot({ path: shotPath });

    console.log(`Viewport ${vp.name}: H-Overflow = ${overflow.hasHorizontalScroll} (scroll: ${overflow.scrollWidth}px, inner: ${overflow.innerWidth}px) -> Saved: vp_${vp.name}.png`);
  }

  await browser.close();
}

main().catch(console.error);
