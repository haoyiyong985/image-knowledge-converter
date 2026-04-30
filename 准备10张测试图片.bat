@echo off
chcp 65001 >nul
echo ==========================================
echo   准备测试批次 - 选择10张图片进行验证
echo ==========================================
echo.

set PROCESSED_DIR=D:\新建文件夹\已处理图片\示范
set PENDING_DIR=D:\新建文件夹\待处理图片\示范
set TEST_BACKUP=D:\新建文件夹\已处理图片\示范_test_backup

:: 创建目录
if not exist "%PENDING_DIR%" mkdir "%PENDING_DIR%"
if not exist "%TEST_BACKUP%" mkdir "%TEST_BACKUP%"

echo 📋 正在准备测试图片...
echo.

:: 复制前10张图片到待处理目录
set count=0
for %%f in ("%PROCESSED_DIR%\*.jpg" "%PROCESSED_DIR%\*.jpeg" "%PROCESSED_DIR%\*.png" "%PROCESSED_DIR%\*.webp") do (
    if !count! lss 10 (
        if exist "%%f" (
            set /a count+=1
            echo   !count!. %%~nxf
            copy "%%f" "%PENDING_DIR%\" >nul
        )
    )
)

echo.
echo ✅ 已准备 %count% 张测试图片
echo 📂 位置: %PENDING_DIR%
echo.
echo ==========================================
echo 💡 下一步操作:
echo    1. 在 ima 中删除旧的混乱文档
echo    2. 在 WorkBuddy 中发送「处理新图片」
echo ==========================================
echo.
pause
