import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';

async function crop() {
  const browser = await puppeteer.launch({
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    headless: true,
  });
  const page = await browser.newPage();
  const imgPath =
    'C:/Users/Admin/.gemini/antigravity/brain/74b615cd-d12e-43a4-943b-840b5ee727c0/.user_uploaded/media_1793280513906_280762ae.png';
  const imgData = fs.readFileSync(imgPath).toString('base64');
  await page.setContent(
    `<html><body style="margin:0;padding:0;background:#000;"><img id="src" src="data:image/png;base64,${imgData}" style="display:block;" /></body></html>`
  );

  const rect = await page.evaluate(() => {
    const img = document.getElementById('src');
    return { width: img.naturalWidth, height: img.naturalHeight };
  });
  console.log('Original image dimensions:', rect);

  await page.setViewport({ width: rect.width, height: rect.height });

  const outDir = 'D:/VIRMS/demo/react/public/vehicles';
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  // In 1024x640:
  // The Jeep card is at top right
  const clip = {
    x: Math.round(rect.width * 0.776),
    y: Math.round(rect.height * 0.222),
    width: Math.round(rect.width * 0.128),
    height: Math.round(rect.height * 0.20),
  };
  console.log('Clip area:', clip);

  await page.screenshot({
    path: path.join(outDir, 'jeep-rubicon.png'),
    clip,
  });

  await browser.close();
  console.log('Cropped successfully!');
}

crop().catch(console.error);
