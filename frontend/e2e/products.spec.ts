import { test, expect } from './fixtures/auth';

test('can view products list', async ({ adminPage }) => {
  await adminPage.goto('/products');
  await expect(adminPage.getByRole('heading', { name: 'Products' })).toBeVisible();
  await expect(adminPage.locator('table')).toBeVisible();
});

test('can add a new product', async ({ adminPage }) => {
  await adminPage.goto('/products');
  await adminPage.getByRole('button', { name: /add product/i }).click();

  const sku = `SKU-E2E-${Date.now()}`;
  await adminPage.getByLabel('SKU').fill(sku);
  await adminPage.getByLabel('Name').fill('Playwright Test Widget');
  await adminPage.getByLabel('Unit price').fill('19.99');
  await adminPage.getByRole('button', { name: /save product/i }).click();

  await expect(adminPage.getByText(sku)).toBeVisible();
});