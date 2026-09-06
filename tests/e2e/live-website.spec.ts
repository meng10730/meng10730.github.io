import { test, expect } from '@playwright/test';

test.describe('線上已部署網站 (https://meng10730.github.io) 實地 E2E 驗收測試', () => {
  const BASE_URL = 'https://meng10730.github.io';

  test('1. 驗證首頁與部落格導覽可存取性', async ({ page }) => {
    // 訪問首頁
    await page.goto(BASE_URL);
    await expect(page).toHaveTitle(/晚餐後的書桌/);
    await expect(page.locator('h1, header').first()).toBeVisible();

    // 訪問部落格頁面
    await page.goto(`${BASE_URL}/blog`);
    await expect(page).toHaveTitle(/觀其文 · 文章專欄/);

    // 驗證四大專欄卡片渲染
    const cards = page.locator('.category-portal-card');
    await expect(cards).toHaveCount(4);

    // 截圖保存首頁與部落格
    await page.screenshot({ path: 'tests/e2e/screenshots/live-blog-verified.png' });
  });

  test('2. 驗證線上 Keystatic 管理後台與即時部署指示燈', async ({ page }) => {
    // 訪問管理後台
    await page.goto(`${BASE_URL}/keystatic`);
    await expect(page).toHaveTitle(/管理後台 \| 晚餐後的書桌/);

    // 驗證返回書桌水墨按鈕
    const backBtn = page.locator('.back-to-site-btn');
    await expect(backBtn).toBeVisible({ timeout: 15000 });
    await expect(backBtn.locator('.btn-stamp-text')).toContainText('返回書桌');

    // 驗證即時部署指示燈存在
    const refreshBtn = page.locator('button[title*="部署狀態"]');
    await expect(refreshBtn).toBeVisible({ timeout: 15000 });

    // 等待指示燈取得狀態
    const statusContainer = refreshBtn.locator('..');
    await expect(statusContainer).toBeVisible({ timeout: 15000 });

    // 測試點擊手動重新整理
    await refreshBtn.click();
    await page.waitForTimeout(1000);

    // 截圖保存管理後台成果
    await page.screenshot({ path: 'tests/e2e/screenshots/live-keystatic-verified.png' });
  });

  test('3. 驗證關於我與作品集靜態頁面', async ({ page }) => {
    await page.goto(`${BASE_URL}/about`);
    await expect(page).toHaveTitle(/關於我/);

    await page.goto(`${BASE_URL}/works`);
    await expect(page).toHaveTitle(/作品集/);
  });
});
