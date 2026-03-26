import { test, expect } from '@playwright/test';

test.describe('Speech Synthesis Flow', () => {
  test('has title and handles text input', async ({ page }) => {
    // Navigate to the synthesis page
    await page.goto('/synthesis');
    
    // Check header
    await expect(page.locator('h1')).toContainText('Speech Synthesis');

    // Wait for backend to be online and voices to load
    const textarea = page.locator('textarea.main-textarea');
    await expect(textarea).toBeVisible();

    // Fill the text
    await textarea.fill('Dies ist ein technischer Test der Quisy-App.');
    
    // Check for the voice dropdown
    const voiceSelect = page.locator('p-select');
    await expect(voiceSelect).toBeVisible();
    
    // The generate button should be present
    const generateBtn = page.locator('button.generate-btn');
    await expect(generateBtn).toBeVisible();
  });
});
