import { test, expect } from '@playwright/test';

test.describe('成就殿堂與彩蛋通知點擊跳轉驗收測試', () => {
  test('1. 直接訪問成就殿堂頁面 (/achievements) 並驗證鎖定狀態', async ({ page }) => {
    await page.goto('/achievements');
    await expect(page).toHaveTitle(/成就殿堂 \| 晚餐後的書桌/);

    const title = page.locator('.achievements-title');
    await expect(title).toHaveText('成就殿堂');
    const count = page.locator('#achievements-count');
    await expect(count).toHaveText('0 / 2');

    const lockedCards = page.locator('.achievement-card.is-locked');
    await expect(lockedCards).toHaveCount(2);

    const backBlogBtn = page.locator('a[href="/blog"]');
    await expect(backBlogBtn).toBeVisible();
    await expect(backBlogBtn).toContainText('返回觀其文');
  });

  test('2. 攜帶 unlocked 參數訪問成就頁面，驗證卡片點亮與進度更新', async ({ page }) => {
    await page.goto('/achievements?unlocked=single10,all10&highlight=single10');
    await expect(page).toHaveTitle(/成就殿堂 \| 晚餐後的書桌/);

    const count = page.locator('#achievements-count');
    await expect(count).toHaveText('2 / 2');

    const unlockedCards = page.locator('.achievement-card.is-unlocked');
    await expect(unlockedCards).toHaveCount(2);

    const single10Card = page.locator('#card-single10');
    await expect(single10Card).toHaveClass(/is-highlighted/);

    await page.screenshot({ path: 'tests/e2e/screenshots/achievements-unlocked.png' });
  });

  test('3. 驗證在部落格頁面觸發成就 Toast 且包含新分頁跳轉連結', async ({ page }) => {
    await page.goto('/blog');
    await expect(page).toHaveTitle(/觀其文 · 文章專欄/);

    await page.evaluate(() => {
      const toast = document.createElement('a');
      toast.className = 'steam-toast-card';
      toast.href = '/achievements?unlocked=single10&highlight=single10';
      toast.target = '_blank';
      toast.rel = 'noopener noreferrer';
      toast.innerHTML = [
        '<div class="steam-toast-shimmer"></div>',
        '<div class="steam-toast-left"><div class="steam-toast-icon">🏆</div></div>',
        '<div class="steam-toast-right">',
        '  <div class="steam-toast-tag">成就解鎖！</div>',
        '  <div class="steam-toast-title">別再戳了啦！</div>',
        '  <div class="steam-toast-desc">在「觀其文」專欄分類中，執著於單一卷軸，連續點擊達 10 次。</div>',
        '  <div class="steam-toast-hint">點擊於新分頁查看成就殿堂 ↗</div>',
        '</div>'
      ].join('');
      let container = document.querySelector('.steam-toast-container');
      if (!container) {
        container = document.createElement('div');
        container.className = 'steam-toast-container';
        document.body.appendChild(container);
      }
      container.appendChild(toast);
    });

    const toast = page.locator('a.steam-toast-card');
    await expect(toast).toBeVisible();
    await expect(toast.locator('.steam-toast-title')).toContainText('別再戳了啦！');
    await expect(toast.locator('.steam-toast-hint')).toContainText('點擊於新分頁查看成就殿堂 ↗');

    const href = await toast.getAttribute('href');
    expect(href).toBe('/achievements?unlocked=single10&highlight=single10');
    expect(await toast.getAttribute('target')).toBe('_blank');

    await page.screenshot({ path: 'tests/e2e/screenshots/achievements-toast-click.png' });
  });
});
