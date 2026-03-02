import { chromium } from 'playwright';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  console.log('Navigating to app...');
  await page.goto('http://localhost:3005/');
  
  // Wait for the upload button
  await page.waitForSelector('text=Upload Photo');
  
  console.log('Uploading photo...');
  const uploadInput = page.locator('input[type="file"]');
  const filePath = path.join(__dirname, 'public', 'test-face.png');
  await uploadInput.setInputFiles(filePath);
  
  // Wait for gallery
  await page.waitForSelector('text=Premium Collection');
  
  console.log('Applying a wig...');
  // Click the 3rd wig (should be a cool realistic one)
  const wigButtons = page.locator('.grid.grid-cols-3 button');
  await wigButtons.nth(2).click();
  
  // Wait a bit for images to render
  await page.waitForTimeout(2000);
  
  // Also tweak scale slightly using the range input if we want
  // Or just leave it as default.
  
  console.log('Taking screenshot...');
  const screenshotPath = path.join(__dirname, 'public', 'demo-result.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  
  await browser.close();
  console.log(`Success! Screenshot saved to ${screenshotPath}`);
})();
