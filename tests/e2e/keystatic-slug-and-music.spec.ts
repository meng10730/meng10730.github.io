import { test, expect } from '@playwright/test';

test.describe('Keystatic Slug 轉譯與作品集音樂播放器驗收測試', () => {
  test('1. 驗證作品集頁面 (/works) 音樂創作與改編專區排版與試聽按鈕', async ({ page }) => {
    await page.goto('/works');
    await expect(page).toHaveTitle(/作品集 \| 晚餐後的書桌/);

    const musicSection = page.locator('#music');
    await expect(musicSection).toBeVisible();
    await expect(musicSection.locator('.category-title')).toContainText('音樂創作與改編');

    const previewBtn = page.locator('.play-music-btn').first();
    await expect(previewBtn).toBeVisible();
    await expect(previewBtn).toContainText('試聽曲目');

    await previewBtn.click();
    const dockBar = page.locator('#music-dock-bar');
    await expect(dockBar).toHaveClass(/active/);

    const songTitle = page.locator('#dock-song-title');
    await expect(songTitle).toBeVisible();

    await page.screenshot({ path: 'tests/e2e/screenshots/works-music-dock-verified.png' });
  });

  test('2. 驗證 Keystatic 後台新增文章頁面之 Slug 必填標記與提示文案', async ({ page }) => {
    await page.goto('/keystatic/collection/blog/create');
    await page.waitForSelector('text=部落格文章', { timeout: 20000 });

    const slugDesc = page.locator('text=輸入標題時將自動轉為拼音');
    await expect(slugDesc.first()).toBeVisible();

    const slugLabel = page.locator('text=網址別名 (Slug)');
    await expect(slugLabel.first()).toBeVisible();

    await page.screenshot({ path: 'tests/e2e/screenshots/keystatic-slug-verified.png' });
  });
});
