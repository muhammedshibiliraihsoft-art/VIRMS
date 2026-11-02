import puppeteer from 'puppeteer';
import path from 'path';

const ARTIFACT_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function verifyWorkspaceBg() {
  console.log('🚀 Verifying Workspace Background...');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });

  // Ensure on Dashboard
  await page.evaluate(() => {
    const tabs = Array.from(document.querySelectorAll('nav[aria-label="Quick section navigation"] button'));
    const dashTab = tabs.find(t => t.textContent?.includes('Overview'));
    if (dashTab) dashTab.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  const bgStyles = await page.evaluate(() => {
    const main = document.querySelector('main.workspace-canvas');
    if (!main) return null;
    const computed = window.getComputedStyle(main);
    return {
      backgroundColor: computed.backgroundColor,
      backgroundImage: computed.backgroundImage,
      border: computed.border,
    };
  });
  console.log('Workspace Background Styles:', bgStyles);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'workspace_bg_warm_wash.png'),
    fullPage: false,
  });

  await browser.close();
  console.log('🎉 Screenshot saved to workspace_bg_warm_wash.png');
}

verifyWorkspaceBg().catch((err) => {
  console.error('Error during verification:', err);
  process.exit(1);
});
