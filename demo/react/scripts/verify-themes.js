import puppeteer from 'puppeteer';

async function verifyThemes() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  const artifactDir = 'C:\\Users\\Admin\\.gemini\\antigravity\\brain\\74b615cd-d12e-43a4-943b-840b5ee727c0';

  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
  await new Promise(r => setTimeout(r, 600));

  // Light Mode Screenshot
  await page.screenshot({ path: `${artifactDir}\\warm_cards_light.png` });
  console.log('Saved warm_cards_light.png');

  // Toggle to Dark Mode via Theme button (the Moon icon in sidebar rail)
  const buttons = await page.$$('aside[aria-label="Sidebar Navigation"] button');
  // The theme button has title "Switch to dark mode"
  for (const b of buttons) {
    const title = await page.evaluate(el => el.getAttribute('title'), b);
    if (title && title.includes('Switch to dark mode')) {
      await b.click();
      break;
    }
  }

  await new Promise(r => setTimeout(r, 600));
  await page.screenshot({ path: `${artifactDir}\\warm_cards_dark.png` });
  console.log('Saved warm_cards_dark.png');

  await browser.close();
}

verifyThemes().catch(console.error);
