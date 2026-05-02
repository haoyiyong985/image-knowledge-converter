@echo off
chcp 65001
cls
echo ============================================
echo  图片知识库工具 - 一键重置到 1.0 版本
echo ============================================
echo.
echo 此脚本将：
echo  1. 备份当前文档到 backup_YYYYMMDD 文件夹
echo  2. 删除所有 .md 文档
echo  3. 将图片移回待处理目录
echo  4. 清理进度文件
echo.
echo 重置后，请在 WorkBuddy 中发送「处理新图片」
echo.
pause

echo.
echo [步骤 1/4] 创建备份...
set backup_dir=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%
set backup_dir=%backup_dir: =0%
mkdir "%backup_dir%"
copy "处理结果\*.md" "%backup_dir%\" >nul 2>&1
echo [OK] 备份完成，位置：%backup_dir%

echo.
echo [步骤 2/4] 删除 .md 文档...
del "处理结果\*.md" /q
echo [OK] 已删除

echo.
echo [步骤 3/4] 将图片移回待处理目录...
for /r "已处理图片" %%f in (*.jpg *.jpeg *.png *.webp *.bmp) do (
    move "%%f" "待处理图片\示范\" >nul 2>&1
)
echo [OK] 图片已移回

echo.
echo [步骤 4/4] 清理进度文件...
del "progress\*.json" /q
echo [OK] 已清理

echo.
echo ============================================
echo  重置完成！
echo ============================================
echo.
echo 接下来：
echo  1. 在 WorkBuddy 中发送「处理新图片」
echo  2. AI 会自动识别、整理、分类
echo.
pause
