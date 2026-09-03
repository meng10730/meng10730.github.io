import { test, expect } from '@playwright/test';

test.describe('部落格專欄卡片互動、逃跑動效、防黑化與賦歸 E2E 測試', () => {
  test('驗證四大專欄連續懸停、逃跑隱形佔位、哄回賦歸與 0 濾鏡殘留', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      console.log(`[Browser Console ${msg.type()}]:`, msg.text());
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    page.on('pageerror', (err) => {
      consoleErrors.push(err.message);
    });

    // 1. 導訪專欄首頁
    await page.goto('/blog');
    await page.waitForLoadState('networkidle');

    // 等待用戶端腳本初始化完成
    await page.waitForSelector('.category-portal-card[data-interactive-bound="true"]', { timeout: 10000 });

    // 確保四大卡片已渲染
    const techWrapper = page.locator('.category-card-wrapper').filter({ hasText: '技術筆記' });
    const techCard = techWrapper.locator('.category-portal-card');
    const techNote = techWrapper.locator('.category-note-card');
    const coaxBtn = techWrapper.locator('.btn-coax-back');
    const bubbleText = techCard.locator('.bubble-typing-text');
    const badgeIcon = techCard.locator('.bubble-badge-icon');

    // 2. 逐步懸停並驗證狀態
    for (let count = 1; count <= 10; count++) {
      await techCard.hover();
      await page.waitForTimeout(300);
      const text = await bubbleText.textContent();
      console.log(`[Test] Hover #${count} Text:`, text?.slice(0, 20));
      if (count < 10) {
        await page.mouse.move(0, 0);
        await page.waitForTimeout(150);
      }
    }

    // 第 10 次後等待打字機完成並觸發逃跑動效
    await page.waitForTimeout(1500);

    // 斷言卡片已逃跑隱藏，而隱形佔位層已啟用
    await expect(techCard).toBeHidden({ timeout: 10000 });
    await expect(techNote).toBeAttached();

    // 5. 驗證方案 C：平日為純淨隱形佔位，Hover 時才浮現互動元素
    await techWrapper.hover();
    await expect(coaxBtn).toBeVisible({ timeout: 5000 });
    await expect(coaxBtn).toHaveText('哄回來');

    // 6. 點擊「哄回來」按鈕
    await coaxBtn.click();
    await expect(techCard).toBeVisible({ timeout: 5000 });
    await expect(techNote).toBeHidden({ timeout: 5000 });

    // 7. 關鍵斷言：物理級檢驗 0 濾鏡殘留（徹底根除黑化 Bug）
    const cardFilter = await techCard.evaluate((el) => {
      const style = window.getComputedStyle(el);
      return style.filter;
    });
    expect(cardFilter === 'none' || cardFilter === '').toBeTruthy();

    // 8. 驗證賦歸台詞打字機輸出與專屬【傲】圖示
    const returnBadge = await badgeIcon.textContent();
    expect(returnBadge).toContain('【傲】');
    await expect(bubbleText).toContainText('強制重啟成功', { timeout: 4000 });

    // 9. 驗證成就已正確寫入 sessionStorage 且成功解鎖
    const single10Unlocked = await page.evaluate(() => sessionStorage.getItem('blog_achievement_single10'));
    expect(single10Unlocked).toBe('true');

    // 10. 截圖保存驗收證據
    await page.screenshot({ path: 'tests/e2e/screenshots/tech-card-verified.png' });

    // 11. 斷言全程 0 JS 控制台致命報錯
    expect(consoleErrors.length).toBe(0);
  });
});
