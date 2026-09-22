import { test as base, expect, type Page } from '@playwright/test';

const ADMIN_EMAIL = 'krish.aot.cse@gmail.com'; // your existing verified admin
const ADMIN_PASSWORD = 'Test@1234'; // adjust to your actual current password

async function loginAsAdmin(page: Page) {
  await page.goto('/login');
  await page.getByLabel('Email').fill(ADMIN_EMAIL);
  await page.getByLabel('Password').fill(ADMIN_PASSWORD);
  await page.getByRole('button', { name: /sign in/i }).click();

  // If OTP is required, this will fail here — flagged in test output rather than hanging
  await expect(page).toHaveURL('/dashboard', { timeout: 10000 });
}

export const test = base.extend<{ adminPage: Page }>({
  adminPage: async ({ page }, use) => {
    await loginAsAdmin(page);
    await use(page);
  },
});

export { expect };