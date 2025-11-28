const { test, expect } = require('@playwright/test');

test.describe('Visual Novel Reader', () => {
    const sentences = [
        'The sun dipped below the horizon.',
        'A cool breeze rustled the leaves.',
        '"Where are we going?" she asked.',
        'He didn\'t answer immediately.',
        'He just pointed towards the old, creaky lighthouse.',
        '"There," he finally said.',
        'Was this a good idea?',
        'Probably not.'
    ];

    test.beforeEach(async ({ page }) => {
        await page.goto('http://localhost:3000');
        await page.evaluate(() => localStorage.clear());
        await page.reload();
        await expect(page.locator('#dialogue')).toHaveText(sentences[0]);
    });

    test('should load the first sentence on initial visit', async ({ page }) => {
        await expect(page.locator('#dialogue')).toHaveText(sentences[0]);
        await expect(page.locator('#btn-continue')).toBeHidden();
    });

    test('should advance to the next sentence on "Next" button click', async ({ page }) => {
        await page.click('#btn-next');
        await expect(page.locator('#dialogue')).toHaveText(sentences[1]);
    });

    test('should save progress and show "Continue" button on reload', async ({ page }) => {
        await page.click('#btn-next');
        await page.click('#btn-next');
        await expect(page.locator('#dialogue')).toHaveText(sentences[2]);

        await page.reload();

        await expect(page.locator('#dialogue')).toHaveText(sentences[0]);
        await expect(page.locator('#btn-continue')).toBeVisible();

        await page.click('#btn-continue');
        await expect(page.locator('#dialogue')).toHaveText(sentences[2]);
        await expect(page.locator('#btn-continue')).toBeHidden();
    });

    test('should restart from the beginning when "Restart" is clicked', async ({ page }) => {
        await page.click('#btn-next');
        await page.click('#btn-next');

        await page.reload();
        await expect(page.locator('#btn-continue')).toBeVisible();

        await page.click('#btn-restart');
        await expect(page.locator('#dialogue')).toHaveText(sentences[0]);

        await page.reload();
        await expect(page.locator('#btn-continue')).toBeHidden();
    });

    test('should hide "Next" button on the last sentence', async ({ page }) => {
        for (let i = 0; i < sentences.length - 1; i++) {
            await page.click('#btn-next');
        }
        await expect(page.locator('#dialogue')).toHaveText(sentences[sentences.length - 1]);
        await expect(page.locator('#btn-next')).toBeHidden();
    });
});