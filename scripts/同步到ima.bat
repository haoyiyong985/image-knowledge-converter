@echo off
chcp 65001 >nul
echo ==========================================
echo   同步文档到 ima
echo ==========================================
echo.

cd /d "D:\新建文件夹"
python ima_sync.py

echo.
pause
