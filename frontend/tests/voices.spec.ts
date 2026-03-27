import { test, expect } from '@playwright/test';

test.describe('Voice Library Flow', () => {
  test('lists voices and opens create dialog', async ({ page }) => {
    await page.goto('/voices');
    
    // Check header
    await expect(page.locator('h1')).toContainText('Voice Library');

    // Wait for create button
    const createBtn = page.locator('button.create-btn');
    await expect(createBtn).toBeVisible();

    // Click on Neue Stimme
    await createBtn.click();

    // Expect Create Dialog to appear
    const dialog = page.locator('p-dialog');
    await expect(dialog).toBeVisible();
    
    // Verify inputs inside dialog
    const nameInput = dialog.locator('input[placeholder="z.B. Podcast-Sprecher"]');
    await expect(nameInput).toBeVisible();
    
    // Close dialog
    const cancelBtn = dialog.locator('button.cancel-btn');
    await cancelBtn.click();
    await expect(dialog).not.toBeVisible();
  });
});
