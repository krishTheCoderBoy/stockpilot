import { test, expect } from './fixtures/auth';

test('full PO lifecycle through the UI', async ({ adminPage }) => {
  // Prereqs: assumes at least one supplier, warehouse, and product already exist (from seed data)
  await adminPage.goto('/purchase-orders');
  await adminPage.getByRole('button', { name: /new purchase order/i }).click();

  await adminPage.locator('select').nth(0).selectOption({ index: 1 }); // supplier
  await adminPage.locator('select').nth(1).selectOption({ index: 1 }); // warehouse
  await adminPage.locator('select').nth(2).selectOption({ index: 1 }); // product
  await adminPage.getByPlaceholder('Qty').fill('10');
  await adminPage.getByPlaceholder('Price').fill('5');
  await adminPage.getByRole('button', { name: /create purchase order/i }).click();

  // Should now be back on the list; open the newly created PO via its "View" button
  await adminPage.getByRole('button', { name: 'View' }).first().click();
  await expect(adminPage.getByText('DRAFT').first()).toBeVisible();

  await adminPage.getByRole('button', { name: /submit for approval/i }).click();
  await expect(adminPage.getByText('SUBMITTED').first()).toBeVisible();

  await adminPage.getByRole('button', { name: /^approve$/i }).click();
  await expect(adminPage.getByText('APPROVED').first()).toBeVisible();

  await adminPage.getByRole('button', { name: /mark as ordered/i }).click();
  await expect(adminPage.getByText('ORDERED').first()).toBeVisible();

  await adminPage.getByRole('button', { name: /receive items/i }).click();
  await adminPage.getByPlaceholder('Qty').fill('10');
  await adminPage.getByRole('button', { name: /confirm receipt/i }).click();
  await expect(adminPage.getByText('RECEIVED').first()).toBeVisible();

  await adminPage.getByRole('button', { name: /close purchase order/i }).click();
  await expect(adminPage.getByText('CLOSED').first()).toBeVisible();
});