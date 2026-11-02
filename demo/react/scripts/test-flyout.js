import puppeteer from 'puppeteer';

async function testFlyout() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://127.0.0.1:5173/');

  const invBtn = await page.$('button[aria-label="Investment Management"]');
  if (invBtn) {
    await invBtn.click();
    await new Promise(r => setTimeout(r, 200));
    const flyoutItems = await page.evaluate(() => {
      const flyout = document.querySelector('[role="region"][aria-label*="submenu"]');
      if (!flyout) return null;
      return Array.from(flyout.querySelectorAll('button')).map(b => b.textContent?.trim());
    });
    console.log('Flyout items:', flyoutItems);
  }
  await browser.close();
}

testFlyout().catch(console.error);
