@echo off
chcp 65001 >nul
title GitHub 推送脚本

echo ========================================
echo   图片转知识库系统 - GitHub 推送
echo ========================================
echo.

:: 进入项目目录
cd /d "%~dp0"

:: 查找 Git
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Git！
    echo 请先安装 Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [1/4] 清理敏感文件...
:: 删除备份文件夹（如果存在）
if exist "knowledge_converter_backup*" (
    rd /s /q "knowledge_converter_backup*"
    echo   已删除备份文件夹
)

:: 替换敏感信息
python -c "import re; import os
files = ['auto_process_ocr.py', 'check_ocr_status.py', 'test_ocr.py']
for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8') as file:
            c = file.read()
        c = re.sub(r\"os\.environ\['TENCENT_SECRET_ID'\]\s*=\s*['\\\"][^'\\\"]+['\\\"]\", \"os.environ['TENCENT_SECRET_ID'] = 'YOUR_SECRET_ID'\", c)
        c = re.sub(r\"os\.environ\['TENCENT_SECRET_KEY'\]\s*=\s*['\\\"][^'\\\"]+['\\\"]\", \"os.environ['TENCENT_SECRET_KEY'] = 'YOUR_SECRET_KEY'\", c)
        with open(f, 'w', encoding='utf-8') as file: file.write(c)
        print(f'已清理: {f}')
" 2>nul

echo [2/4] 提交代码...
git add .
git commit -m "Update: 清理敏感信息并同步代码" >nul 2>&1
if %errorlevel% equ 0 (
    echo   提交完成
) else (
    echo   没有新内容
)

echo [3/4] 推送到 GitHub...
echo   (请输入 GitHub 用户名和密码)
echo   用户名: cuixiaohui985
echo   密码: GitHub Personal Access Token ^(不是登录密码^)
echo.

git push -u origin master --force

echo.
echo ========================================
if %errorlevel% equ 0 (
    echo   推送成功！
    echo   请访问: https://github.com/cuixiaohui985/image-knowledge-converter
) else (
    echo   推送失败，请检查错误信息
)
echo ========================================
echo.
pause
