/**
 * UI Tests for Chat Room Application
 *
 * These tests verify the user interface and interactions for the chat room.
 * Tests use Playwright for browser automation.
 *
 * Requirements:
 * - Server must be running on http://localhost:3000
 * - Page should have form inputs for username and message
 * - Page should display posted messages
 * - Form submission should add new messages dynamically
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:3000';

test.describe('Chat Room UI Tests', () => {

  test('should load page and display chat room interface', async ({ page }) => {
    // Navigate to the chat room
    await page.goto(BASE_URL);

    // Verify page has a form with username input
    const usernameInput = page.locator('input[name="username"], input[id="username"], input[placeholder*="name" i]').first();
    await expect(usernameInput).toBeVisible();

    // Verify page has a message input (could be input or textarea)
    const messageInput = page.locator('input[name="message"], input[name="text"], textarea[name="message"], textarea[name="text"], input[id="message"], textarea[id="message"]').first();
    await expect(messageInput).toBeVisible();

    // Verify page has a submit button
    const submitButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Send"), button:has-text("Post"), button:has-text("Submit")').first();
    await expect(submitButton).toBeVisible();
  });

  test('should display messages on the page', async ({ page, request }) => {
    // First, post a message via API (setup)
    await request.post(`${BASE_URL}/api/message`, {
      data: {
        username: 'TestUser',
        text: 'This is a test message'
      }
    });

    // Navigate to the page
    await page.goto(BASE_URL);

    // Wait for messages to load
    await page.waitForTimeout(1000);

    // Verify the message text is visible
    await expect(page.locator('text=This is a test message')).toBeVisible();

    // Verify the username is visible
    await expect(page.locator('text=TestUser')).toBeVisible();
  });

  test('should submit message via form and display it', async ({ page }) => {
    // Navigate to the page
    await page.goto(BASE_URL);

    // Find form inputs
    const usernameInput = page.locator('input[name="username"], input[id="username"], input[placeholder*="name" i]').first();
    const messageInput = page.locator('input[name="message"], input[name="text"], textarea[name="message"], textarea[name="text"], input[id="message"], textarea[id="message"]').first();
    const submitButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Send"), button:has-text("Post"), button:has-text("Submit")').first();

    // Fill in the form
    await usernameInput.fill('UITestUser');
    await messageInput.fill('Message from UI test');

    // Submit the form
    await submitButton.click();

    // Wait for the message to appear (allow time for AJAX/page update)
    await page.waitForTimeout(2000);

    // Verify the message appears on the page
    await expect(page.locator('text=Message from UI test')).toBeVisible();
    await expect(page.locator('text=UITestUser')).toBeVisible();
  });

  test('should display multiple messages in the chat', async ({ page, request }) => {
    // Post multiple messages via API
    const messages = [
      { username: 'Alice', text: 'Hello everyone!' },
      { username: 'Bob', text: 'Hi how are you doing?' },
      { username: 'Charlie', text: 'Good morning!' }
    ];

    for (const msg of messages) {
      await request.post(`${BASE_URL}/api/message`, { data: msg });
    }

    // Navigate to the page
    await page.goto(BASE_URL);

    // Wait for messages to load
    await page.waitForTimeout(1000);

    // Verify all messages are visible
    for (const msg of messages) {
      await expect(page.locator(`text=${msg.text}`)).toBeVisible();
      await expect(page.locator(`text=${msg.username}`)).toBeVisible();
    }
  });

});
