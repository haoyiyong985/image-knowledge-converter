@echo off
chcp 65001 >nul
echo ==========================================
echo   归档测试图片
echo ==========================================
echo.

set PENDING_DIR=D:\新建文件夹\待处理图片\示范
set PROCESSED_DIR=D:\新建文件夹\已处理图片\示范

:: 确保目录存在
if not exist "%PROCESSED_DIR%" mkdir "%PROCESSED_DIR%"

echo 📋 正在归档图片...
echo.

:: 移动所有图片文件
set count=0
for %%f in ("%PENDING_DIR%\*.jpg" "%PENDING_DIR%\*.jpeg" "%PENDING_DIR%\*.png" "%PENDING_DIR%\*.webp") do (
    if exist "%%f" (
        set /a count+=1
        move "%%f" "%PROCESSED_DIR%\" >nul
        echo   ✓ %%~nxf
    )
)

echo.
echo ✅ 已归档 %count% 张图片
echo 📂 位置: %PROCESSED_DIR%
echo.
pause
