import puppeteer from 'puppeteer';

async function test() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  const viewports = [
    { width: 1920, height: 1080 },
    { width: 1600, height: 900 },
    { width: 1440, height: 900 },
    { width: 1366, height: 768 },
    { width: 1280, height: 800 }
  ];

  for (const vp of viewports) {
    await page.setViewport(vp);
    await page.goto('http://127.0.0.1:5173/', { waitUntil: 'domcontentloaded' });
    await new Promise(r => setTimeout(r, 600));

    const check = await page.evaluate((vpWidth) => {
      const container = document.querySelector('.max-w-\\[1480px\\]');
      const containerRect = container?.getBoundingClientRect();
      const calculatedLeft = Math.max(20, (vpWidth - 1480) / 2);
      return {
        vpWidth,
        containerLeft: containerRect ? containerRect.left : null,
        calculatedLeft
      };
    }, vp.width);

    console.log(`VP ${vp.width}: Container Left = ${check.containerLeft}, Calculated Left = ${check.calculatedLeft}, Diff = ${Math.abs(check.containerLeft - check.calculatedLeft)}`);
  }

  await browser.close();
}

test().catch(console.error);
