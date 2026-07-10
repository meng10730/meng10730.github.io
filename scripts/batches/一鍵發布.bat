@echo off
chcp 65001 > nul

echo =========================================
echo      Changshengjie Novel Sync ^& Publish
echo =========================================
echo.

:: 1. Environment dependencies pre-check
echo [1/5] Checking environment dependencies...
where node >nul 2>nul
if %errorlevel% neq 0 goto NODE_MISSING

where git >nul 2>nul
if %errorlevel% neq 0 goto GIT_MISSING

echo   Dependencies check passed!
echo.
goto ENVIRONMENT_CHECK_DONE

:NODE_MISSING
echo [Error] Node.js is not installed or not in PATH.
echo Please install Node.js from https://nodejs.org/ and try again.
pause
exit /b 1

:GIT_MISSING
echo [Error] Git is not installed or not in PATH.
echo Please install Git from https://git-scm.com/ and try again.
pause
exit /b 1

:ENVIRONMENT_CHECK_DONE


:: 2. Git index.lock lock defense
echo [2/5] Check Git index lock status...
if not exist ".git\index.lock" goto LOCK_CHECK_DONE
echo [Warning] Detected Git index lock file [.git/index.lock].
echo Attempting to remove it to prevent blocking...
del /f /q ".git\index.lock" >nul 2>nul
if exist ".git\index.lock" goto LOCK_REMOVE_FAILED
echo   Lock file removed successfully.
goto LOCK_CHECK_DONE

:LOCK_REMOVE_FAILED
echo [Error] Failed to remove .git/index.lock.
echo Please close any other Git clients or IDEs and try again.
pause
exit /b 1

:LOCK_CHECK_DONE
echo.


:: 3. Run glossary and anti-AI pre-check
echo [3/5] Running website glossary and anti-AI checks...
node scripts/check-glossary.js
if %errorlevel% neq 0 goto CHECK_FAILED
echo   Glossary check completed!
echo.
goto CHECK_DONE

:CHECK_FAILED
echo.
echo [Error] Glossary check script failed with an execution error!
echo.
pause
exit /b 1

:CHECK_DONE


:: 4. Scan changes and handle Commit
echo [4/5] Scanning changed files...
git add .

set "HAS_CHANGES="
for /f "tokens=*" %%i in ('git status --porcelain') do set "HAS_CHANGES=1"

set "NEED_PUSH="
for /f "tokens=*" %%i in ('git cherry -v 2^>nul') do set "NEED_PUSH=1"

if not defined HAS_CHANGES goto SKIP_COMMIT
git status -s
echo.
set /p msg="Enter commit message [Press Enter for default: 'Auto-sync novels']: "
if "%msg%"=="" set msg=Auto-sync novels

echo.
echo Saving changes [Commit]...
git commit -m "%msg%"
set "NEED_PUSH=1"
goto COMMIT_DONE

:SKIP_COMMIT
echo   No changes detected in local files. Skip commit.

:COMMIT_DONE
echo.


:: 5. Defensive pull and push
if not defined NEED_PUSH goto SKIP_PUSH

echo [5/5] Testing connection to remote GitHub repository...
git ls-remote --exit-code -h origin >nul 2>nul
if %errorlevel% neq 0 goto OFFLINE_MODE

echo Pulling latest changes from remote (Rebase)...
git pull --rebase
if %errorlevel% neq 0 goto PULL_CONFLICT

echo.
echo Uploading to GitHub [Push]...
git push
if %errorlevel% neq 0 goto PUSH_FAILED

echo.
echo ====================================================
echo  上傳成功！已順利推送至 GitHub 遠端倉庫。
echo  正在為您追蹤 GitHub Actions 線上自動部署狀態...
echo ====================================================
echo.
node scripts/check-action-status.js
goto PUSH_DONE

:OFFLINE_MODE
echo [Offline Mode] Sync completed locally, but skipped remote upload due to network offline or authentication failure.
echo.
echo =========================================
echo  Offline success! Local changes saved.
echo =========================================
echo.
pause
exit /b 0

:PULL_CONFLICT
echo.
echo [Error] Conflict detected during git pull --rebase!
echo.
git rebase --abort >nul 2>nul
for /f "tokens=*" %%i in ('powershell -Command "Get-Date -Format 'yyyyMMdd_HHmmss'"') do set "TS=%%i"
git branch backup/conflict-%TS% >nul 2>nul
echo ============================================================
echo                 CONFLICT RESOLUTION GUIDE
echo ============================================================
echo  1. The auto-publish process has been safely aborted.
echo  2. A backup branch [backup/conflict-%TS%] has been created
echo     to preserve your local commit changes.
echo  3. To resolve this conflict manually:
echo     a. Run: git pull origin main
echo     b. Open conflicted files and resolve the merge markers.
echo     c. Run: git add .
echo     d. Run: git commit -m "Merge and resolve conflicts"
echo     e. Run the publish batch file again to publish your changes.
echo ============================================================
echo.
pause
exit /b 1

:PUSH_FAILED
echo.
echo [Error] Failed to push changes to GitHub!
echo.
pause
exit /b 1

:SKIP_PUSH
echo [5/5] Skip push [no local changes or unsent commits].
echo.
echo =========================================
echo  Nothing to publish. Everything is up to date!
echo =========================================

:PUSH_DONE
echo.
pause
