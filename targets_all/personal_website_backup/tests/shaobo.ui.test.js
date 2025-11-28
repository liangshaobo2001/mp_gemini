const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('Shaobo\'s Personal Website UI Tests', () => {

  test('should display correct content for Shaobo\'s website', async ({ page }) => {
    const response = await page.goto(BASE_URL);
    expect(response.status()).toBe(200);

    // Check page title
    await expect(page).toHaveTitle(/Shaobo's Personal Website/);

    // Check H1
    await expect(page.locator('h1')).toHaveText('Shaobo');

    // Check About Me section
    await expect(page.locator('#about p')).toContainText('I am a programmer (Python), philosopher, and creative writer');

    // Check Writing section
    await expect(page.locator('#writing h2')).toHaveText('Creative Writing');
    await expect(page.locator('#writing p')).toContainText('I write hardcore science fiction');
  });

});