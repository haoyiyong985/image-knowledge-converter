@echo off
chcp 65001 > nul
title GitHub Push

echo ====================
echo  GitHub Push Tool
echo ====================
echo.

set /p TOKEN=Enter GitHub Token: 
if "%TOKEN%"=="" (
    echo [ERROR] Token cannot be empty!
    pause
    exit /b 1
)

cd /d "d:\新建文件夹"
echo [1/4] Working directory: d:\新建文件夹

echo [2/4] Configuring remote...
git remote remove origin 2>nul
git remote add origin https://cuixiaohui985:%TOKEN%@github.com/cuixiaohui985/image-knowledge-converter.git
echo   Remote configured.

echo [3/4] Committing changes...
git add .
git diff --quiet
if errorlevel 1 (
    git commit -m "Update: sync"
    echo   Changes committed.
) else (
    echo   No changes to commit.
)

echo [4/4] Pushing to GitHub...
git push -u origin master --force 2>&1
if errorlevel 1 (
    echo.
    echo [FAILED] Push failed! Check Token and network.
) else (
    echo.
    echo [SUCCESS] Push completed!
    echo   Visit: https://github.com/cuixiaohui985/image-knowledge-converter
)
echo.
pause
