@echo off
chcp 65001 > nul

echo ==========================================
echo   還原 Keystatic 開發環境設定 (Hybrid 模式)
echo ==========================================
echo.
echo 正在還原 src/pages/keystatic/[...params].astro 檔案...

powershell -Command "$content = @'\
---
import { KeystaticApp } from '../../components/KeystaticApp.tsx';

export const prerender = false;
---
<script is:inline>
  (function() {
    var params = new URLSearchParams(window.location.search);
    var redirectUrl = params.get('redirect');
    if (redirectUrl) {
      window.history.replaceState(null, '', redirectUrl);
    }
  })();
</script>
<KeystaticApp client:only="react" />
'@; [System.IO.File]::WriteAllText('src/pages/keystatic/[...params].astro', $content, [System.Text.Encoding]::UTF8)"

echo.
echo [成功] 開發環境檔案已順利還原！
echo 現在您可以正常執行「開啟編輯器.bat」或「npm run dev」。
echo.
pause
