import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Wig Editor Client App', () => {

  test('should load the home page with title', async ({ page }) => {
    await page.goto('http://localhost:3005');
    await expect(page.locator('h1')).toContainText('Try On Wigs');
    await expect(page.locator('text=Upload Photo')).toBeVisible();
    await expect(page.locator('text=Start Camera')).toBeVisible();
  });

  test('should allow photo upload and display wig options', async ({ page }) => {
    await page.goto('http://localhost:3005');
    
    // Create a dummy image for upload
    const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('text=Upload Photo');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test.png',
      mimeType: 'image/png',
      buffer: buffer
    });

    // Wigs list should now appear
    await expect(page.locator('text=Choose Wig')).toBeVisible();
    await expect(page.locator('img[alt="Blonde Bob"]')).toBeVisible();
    await expect(page.locator('img[alt="Brown Long"]')).toBeVisible();
    await expect(page.locator('img[alt="Black Afro"]')).toBeVisible();
    
    // User image should be rendered
    await expect(page.locator('img[alt="User"]')).toBeVisible();
  });

  test('should allow selecting a wig and show adjustment controls', async ({ page }) => {
    await page.goto('http://localhost:3005');
    
    // Upload image
    const buffer = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('text=Upload Photo');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test.png',
      mimeType: 'image/png',
      buffer: buffer
    });

    // Click a wig
    await page.click('img[alt="Blonde Bob"]');
    
    // Check if the wig is overlaid
    await expect(page.locator('img[alt="Wig"]')).toBeVisible();
    
    // Check if adjustment controls appear
    await expect(page.locator('text=Adjust')).toBeVisible();
    await expect(page.locator('text=Scale')).toBeVisible();
    await expect(page.locator('text=Rotate')).toBeVisible();
  });
});
