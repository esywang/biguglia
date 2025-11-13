import { test, expect } from '@playwright/test';

// Generate unique email for each test run
const generateTestEmail = () => `test-${Date.now()}@example.com`;
const TEST_PASSWORD = 'testpassword123';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Start at the home page (should redirect to login if not authenticated)
    await page.goto('/');
  });

  test('should redirect unauthenticated user to login page', async ({ page }) => {
    // Should be redirected to login
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  });

  test('should display signup page with form', async ({ page }) => {
    await page.goto('/signup');

    // Check for signup form elements
    await expect(page.getByRole('heading', { name: 'Create an account' })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password', { exact: true })).toBeVisible();
    await expect(page.getByLabel('Confirm Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Create account' })).toBeVisible();
  });

  test('should show error for password mismatch on signup', async ({ page }) => {
    await page.goto('/signup');

    const email = generateTestEmail();

    // Fill form with mismatched passwords
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel('Confirm Password').fill('differentpassword');

    // Submit form
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should show error
    await expect(page.getByText('Passwords do not match')).toBeVisible();
  });

  test('should show error for short password on signup', async ({ page }) => {
    await page.goto('/signup');

    const email = generateTestEmail();

    // Fill form with short password
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill('123');
    await page.getByLabel('Confirm Password').fill('123');

    // Submit form
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should show error
    await expect(page.getByText('Password must be at least 6 characters')).toBeVisible();
  });

  test('should successfully sign up a new user', async ({ page }) => {
    await page.goto('/signup');

    const email = generateTestEmail();

    // Fill signup form
    await page.getByLabel('Email').fill(email);
    await page.getByLabel('Password', { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel('Confirm Password').fill(TEST_PASSWORD);

    // Submit form
    await page.getByRole('button', { name: 'Create account' }).click();

    // Should show confirmation message
    await expect(page.getByRole('heading', { name: 'Check your email' })).toBeVisible();
    await expect(page.getByText(/sent you a confirmation email/i)).toBeVisible();
  });

  test('should display login form', async ({ page }) => {
    await page.goto('/login');

    // Check for login form elements
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Try to login with invalid credentials
    await page.getByLabel('Email').fill('invalid@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Should show error (Supabase returns "Invalid login credentials")
    await expect(page.locator('text=/invalid/i')).toBeVisible({ timeout: 5000 });
  });

  test('should navigate between login and signup pages', async ({ page }) => {
    await page.goto('/login');

    // Click signup link
    await page.getByRole('link', { name: 'Sign up' }).click();
    await expect(page).toHaveURL('/signup');
    await expect(page.getByRole('heading', { name: 'Create an account' })).toBeVisible();

    // Click back to login
    await page.getByRole('link', { name: 'Sign in' }).click();
    await expect(page).toHaveURL('/login');
    await expect(page.getByRole('heading', { name: 'Sign in' })).toBeVisible();
  });

  test('should disable form during submission', async ({ page }) => {
    await page.goto('/login');

    // Fill form
    await page.getByLabel('Email').fill('test@example.com');
    await page.getByLabel('Password').fill('password123');

    // Submit form
    const submitButton = page.getByRole('button', { name: 'Sign in' });
    await submitButton.click();

    // Button should show loading state
    await expect(submitButton).toHaveText('Signing in...');
    await expect(submitButton).toBeDisabled();
  });
});

test.describe('Authenticated User', () => {
  // Note: These tests would require setting up a test user with confirmed email
  // For a full test, you'd need to:
  // 1. Create a test user beforehand
  // 2. Or mock the Supabase auth state
  // 3. Or use Supabase test helpers to bypass email confirmation

  test.skip('should login and access protected routes', async ({ page }) => {
    // This test is skipped as it requires a confirmed user account
    // To implement:
    // 1. Create a test user with confirmed email in Supabase
    // 2. Login with that user
    // 3. Verify redirect to home page
    // 4. Verify sidebar shows user email
    // 5. Test logout functionality
  });
});
