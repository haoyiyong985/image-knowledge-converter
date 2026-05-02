@echo off
chcp 65001
cls
echo ==========================================
echo Tesseract OCR 自动安装脚本
echo ==========================================
echo.

:: 创建安装目录
set "INSTALL_DIR=C:\Program Files\Tesseract-OCR"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [1/4] 正在下载 Tesseract 安装包...
echo 下载地址: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe
echo.
echo 由于网络限制，请手动下载并安装：
echo.
echo 1. 打开浏览器访问：
echo    https://digi.bib.uni-mannheim.de/tesseract/
echo.
echo 2. 下载最新版本（如 tesseract-ocr-w64-setup-5.3.0.20221214.exe）
echo.
echo 3. 运行安装程序，按以下步骤操作：
echo    - 选择安装语言：English
echo    - 同意许可协议
echo    - 选择安装路径：C:\Program Files\Tesseract-OCR
echo    - ★★★ 重要：勾选 "Chinese (Simplified)" 语言包 ★★★
echo    - 完成安装
echo.
echo 4. 安装完成后，按任意键继续...
pause

echo.
echo [2/4] 检查安装...
if exist "%INSTALL_DIR%\tesseract.exe" (
    echo [OK] Tesseract 已安装
) else (
    echo [FAIL] 未找到 Tesseract，请确认安装路径：%INSTALL_DIR%
    pause
    exit /b 1
)

echo.
echo [3/4] 添加到系统 PATH...
setx /M PATH "%PATH%;%INSTALL_DIR%"
echo [OK] 已添加到系统 PATH（需要重启命令行生效）

echo.
echo [4/4] 安装 Python 依赖...
pip install pytesseract pillow
echo [OK] Python 依赖安装完成

echo.
echo ==========================================
echo 安装完成！
echo ==========================================
echo.
echo 请重启命令行或电脑，然后运行以下命令测试：
echo   tesseract --version
echo.
pause
