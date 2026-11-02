import puppeteer from 'puppeteer';
import path from 'path';

const ARTIFACT_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function verifySolidCards() {
  console.log('🚀 Verifying Solid Formal Dashboard Cards...');
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

  // Inspect card computed styles
  const cardStyles = await page.evaluate(() => {
    const card = document.querySelector('.dashboard-card-solid');
    if (!card) return null;
    const computed = window.getComputedStyle(card);
    return {
      backgroundColor: computed.backgroundColor,
      backgroundImage: computed.backgroundImage,
      border: computed.border,
      boxShadow: computed.boxShadow,
      backdropFilter: computed.backdropFilter,
    };
  });
  console.log('Light Mode Card Computed Styles:', cardStyles);

  // Capture Light Mode screenshot
  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'solid_cards_dashboard_light.png'),
    fullPage: false,
  });

  // Switch to Dark Mode
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const themeBtn = buttons.find(b => b.title?.includes('Switch to') || b.querySelector('svg.lucide-moon') || b.querySelector('svg.lucide-sun'));
    if (themeBtn) themeBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  // Inspect Dark Mode card computed styles
  const darkCardStyles = await page.evaluate(() => {
    const card = document.querySelector('.dashboard-card-solid');
    if (!card) return null;
    const computed = window.getComputedStyle(card);
    return {
      backgroundColor: computed.backgroundColor,
      backgroundImage: computed.backgroundImage,
      border: computed.border,
      boxShadow: computed.boxShadow,
      backdropFilter: computed.backdropFilter,
    };
  });
  console.log('Dark Mode Card Computed Styles:', darkCardStyles);

  // Capture Dark Mode screenshot
  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'solid_cards_dashboard_dark.png'),
    fullPage: false,
  });

  // Switch back to Light Mode
  await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const themeBtn = buttons.find(b => b.title?.includes('Switch to') || b.querySelector('svg.lucide-moon') || b.querySelector('svg.lucide-sun'));
    if (themeBtn) themeBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  await browser.close();
  console.log('🎉 Solid cards verification complete!');
}

verifySolidCards().catch((err) => {
  console.error('Error during verification:', err);
  process.exit(1);
});
