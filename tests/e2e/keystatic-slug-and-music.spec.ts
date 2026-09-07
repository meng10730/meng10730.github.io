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

  test('2. 驗證 Keystatic 後台新增文章頁面之 Slug 必填標記、輸入標題自動轉譯與 Regenerate 按鈕', async ({ page }) => {
    await page.goto('/keystatic/collection/blog/create');
    await page.waitForSelector('text=部落格文章', { timeout: 20000 });

    const slugDesc = page.locator('text=輸入標題時將自動轉為拼音');
    await expect(slugDesc.first()).toBeVisible();

    const slugLabel = page.locator('text=網址別名 (Slug)');
    await expect(slugLabel.first()).toBeVisible();

    // 驗證輸入標題即時自動生成 Slug
    const inputs = page.locator('input');
    const titleInput = inputs.nth(0);
    const slugInput = inputs.nth(1);

    await titleInput.fill('測試標題自動生成拼音別名');
    await page.waitForTimeout(1000);

    const slugVal = await slugInput.inputValue();
    console.log('E2E 生成的 Slug:', slugVal);
    expect(slugVal).toBe('ce-shi-biao-ti-zi-dong-sheng-cheng-pin-yin');

    // 驗證點擊 Regenerate 按鈕能隨時重新生成
    await slugInput.fill('');
    const regenBtn = page.locator('button:has-text("Regenerate")');
    await regenBtn.first().click();
    await page.waitForTimeout(1000);

    const regeneratedVal = await slugInput.inputValue();
    console.log('E2E Regenerate 後的 Slug:', regeneratedVal);
    expect(regeneratedVal).toBe('ce-shi-biao-ti-zi-dong-sheng-cheng-pin-yin');

    await page.screenshot({ path: 'tests/e2e/screenshots/keystatic-slug-verified.png' });
  });
});
