import puppeteer from 'puppeteer';
import path from 'path';

const ARTIFACT_DIR = 'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0';

async function verifyVehicleDetail() {
  console.log('🚀 Starting Puppeteer Verification for Vehicle Detail View & Image Slot...');
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--force-device-scale-factor=1'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900, deviceScaleFactor: 1 });
  await page.goto('http://127.0.0.1:5173/', { waitUntil: 'networkidle0' });

  // 1. Navigate to Vehicles
  console.log('Navigating to Vehicles...');
  const vehiclesButton = await page.$('button[aria-label="Vehicles"]');
  if (vehiclesButton) await vehiclesButton.click();
  await new Promise((r) => setTimeout(r, 400));

  // 2. Click "Details" on first vehicle (v-6: kl10aj1234 v2)
  console.log('Clicking Details on v-6 (IMAGE 2 source vehicle)...');
  await page.evaluate(() => {
    const detailButtons = Array.from(document.querySelectorAll('button')).filter((b) =>
      b.textContent?.includes('Details')
    );
    if (detailButtons.length > 0) detailButtons[0].click();
  });
  // Close any rail flyout by clicking on main canvas
  await page.mouse.click(600, 300);
  await new Promise((r) => setTimeout(r, 400));

  // Verify content matching IMAGE 2
  const v6Detail = await page.evaluate(() => {
    const title = document.querySelector('h1')?.textContent?.trim();
    const eyebrow = document.querySelector('div.text-\\[10px\\].font-extrabold')?.textContent?.trim();
    const subtitle = document.querySelector('h1 + p')?.textContent?.trim();
    const summaryCards = Array.from(
      document.querySelectorAll('div.grid.grid-cols-1.sm\\:grid-cols-2.lg\\:grid-cols-5 > div')
    ).map((card, i) => {
      const rect = card.getBoundingClientRect();
      return {
        index: i,
        text: card.textContent?.trim().replace(/\s+/g, ' '),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        top: Math.round(rect.top),
        bottom: Math.round(rect.bottom),
      };
    });

    const garageHistoryText = document.querySelector('div.dashboard-card-solid.rounded-\\[22px\\]')?.textContent?.trim();

    return {
      title,
      eyebrow,
      subtitle,
      summaryCardsCount: summaryCards.length,
      summaryCards,
      garageHistoryText,
    };
  });

  console.log('v-6 Vehicle Detail Verification:');
  console.log(' - Title:', v6Detail.title);
  console.log(' - Eyebrow:', v6Detail.eyebrow);
  console.log(' - Subtitle:', v6Detail.subtitle);
  console.log(' - Total Top Cards (including image slot):', v6Detail.summaryCardsCount);
  console.log(' - Card Metrics (checking height alignment & bottom level):');
  v6Detail.summaryCards.forEach((c) => {
    console.log(`   Card ${c.index + 1}: height=${c.height}px, bottom=${c.bottom}px, text=${c.text?.slice(0, 35)}...`);
  });

  // Calculate bottom difference between card 5 (image) and cards 1-4
  const card1Bottom = v6Detail.summaryCards[0]?.bottom;
  const card5Bottom = v6Detail.summaryCards[4]?.bottom;
  const bottomDiff = Math.abs((card5Bottom || 0) - (card1Bottom || 0));
  console.log(` - Bottom alignment delta between image card and summary cards: ${bottomDiff}px (should be <= 2px)`);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'vehicle_detail_v6_placeholder_1440.png'),
    fullPage: false,
  });

  // 3. Test back navigation and opening vehicle with image (v-1: KL 11 AB 4821 Jeep)
  console.log('Navigating back to vehicles and opening v-1 (Jeep with image)...');
  await page.evaluate(() => {
    const backBtn = Array.from(document.querySelectorAll('button')).find((b) =>
      b.textContent?.includes('Back to Vehicles')
    );
    if (backBtn) backBtn.click();
  });
  await new Promise((r) => setTimeout(r, 400));

  // Find and click details on KL 11 AB 4821
  await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll('.grid > div'));
    const jeepCard = cards.find((c) => c.textContent?.includes('KL 11 AB 4821'));
    if (jeepCard) {
      const btn = jeepCard.querySelector('button');
      if (btn) btn.click();
    }
  });
  // Close any flyout
  await page.mouse.click(600, 300);
  await new Promise((r) => setTimeout(r, 400));

  const jeepDetail = await page.evaluate(() => {
    const title = document.querySelector('h1')?.textContent?.trim();
    const img = document.querySelector('img[alt*="Jeep"]');
    const jobsCount = document.querySelectorAll('div.dashboard-card-solid.rounded-\\[22px\\] .bg-white')?.length;
    return {
      title,
      hasImage: Boolean(img),
      imageSrc: img?.getAttribute('src'),
      jobsCount,
    };
  });
  console.log('v-1 Jeep Detail Verification:');
  console.log(' - Title:', jeepDetail.title);
  console.log(' - Image rendered:', jeepDetail.hasImage, jeepDetail.imageSrc);
  console.log(' - Jobs rendered in Garage history:', jeepDetail.jobsCount);

  await page.screenshot({
    path: path.join(ARTIFACT_DIR, 'vehicle_detail_jeep_image_1440.png'),
    fullPage: false,
  });

  // 4. Responsive Verification
  const viewports = [
    { name: '1920x1080', width: 1920, height: 1080 },
    { name: '1280x800', width: 1280, height: 800 },
    { name: 'tablet_768', width: 768, height: 1024 },
    { name: 'mobile_375', width: 375, height: 812 },
  ];

  for (const vp of viewports) {
    await page.setViewport({ width: vp.width, height: vp.height, deviceScaleFactor: 1 });
    await new Promise((r) => setTimeout(r, 200));

    const check = await page.evaluate(() => {
      return {
        hasOverflow: document.documentElement.scrollWidth > window.innerWidth,
        docWidth: document.documentElement.scrollWidth,
        winWidth: window.innerWidth,
      };
    });

    console.log(`Viewport ${vp.name}: overflow=${check.hasOverflow} (${check.docWidth}px / ${check.winWidth}px)`);
    await page.screenshot({
      path: path.join(ARTIFACT_DIR, `vehicle_detail_${vp.name}.png`),
      fullPage: false,
    });
  }

  await browser.close();
  console.log('🎉 Vehicle Detail Verification Complete!');
}

verifyVehicleDetail().catch((err) => {
  console.error('Error during verification:', err);
  process.exit(1);
});
