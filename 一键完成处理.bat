@echo off
chcp 65001 >nul
echo ==========================================
echo   一键完成图片处理流程
echo ==========================================
echo.

cd /d "D:\新建文件夹"

echo [1/4] 📷 识别图片内容...
echo     （已在AI处理中完成）
echo.

echo [2/4] 📝 整理编辑内容...
echo     （已在AI处理中完成）
echo.

echo [3/4] 📂 归档图片...
set PENDING_DIR=D:\新建文件夹\待处理图片\示范
set PROCESSED_DIR=D:\新建文件夹\已处理图片\示范

if not exist "%PROCESSED_DIR%" mkdir "%PROCESSED_DIR%"

set count=0
for %%f in ("%PENDING_DIR%\*.jpg" "%PENDING_DIR%\*.jpeg" "%PENDING_DIR%\*.png" "%PENDING_DIR%\*.webp") do (
    if exist "%%f" (
        set /a count+=1
        move "%%f" "%PROCESSED_DIR%\" >nul
        echo     ✓ %%~nxf
    )
)
echo     已归档 %count% 张图片
echo.

echo [4/4] ☁️ 同步到 ima...
python ima_sync.py
echo.

echo ==========================================
echo ✅ 处理完成！
echo ==========================================
echo.
pause
