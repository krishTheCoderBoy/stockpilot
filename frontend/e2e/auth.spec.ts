import { test, expect } from '@playwright/test';

test('shows landing page when logged out', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText(/know exactly what's in stock/i)).toBeVisible({ timeout: 15000 });
});

test('rejects invalid login', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Email').fill('nobody@test.com');
  await page.getByLabel('Password').fill('wrongpass');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page.getByText(/invalid email or password/i)).toBeVisible();
});

test('redirects unauthenticated user away from dashboard', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveURL('/login');
});