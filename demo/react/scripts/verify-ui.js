import puppeteer from 'puppeteer';
import path from 'node:path';

async function main() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
  });

  const page = await browser.newPage();
  // Standard desktop viewport 1440x1024
  await page.setViewport({ width: 1440, height: 1024, deviceScaleFactor: 2 });

  page.on('console', msg => console.log('BROWSER CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', err => console.error('BROWSER ERROR:', err));

  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });

  const artifactPath = path.resolve('C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/current_render.png');
  await page.screenshot({ path: artifactPath, fullPage: false });

  console.log('Screenshot saved to:', artifactPath);
  await browser.close();
}

main().catch(console.error);
