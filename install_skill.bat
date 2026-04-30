@echo off
chcp 65001 > nul
echo.
echo ======================================
echo   安装图片知识库转化工具 Skill
echo ======================================
echo.

REM 创建目录
if not exist "C:\Users\LENOVO\.workbuddy\skills\image-knowledge-converter" (
    mkdir "C:\Users\LENOVO\.workbuddy\skills\image-knowledge-converter"
    echo [创建] 目录已创建
)

REM 复制文件
copy /Y "D:\新建文件夹\image-knowledge-converter\SKILL.md" "C:\Users\LENOVO\.workbuddy\skills\image-knowledge-converter\SKILL.md"

echo.
echo [完成] Skill 已安装到:
echo        C:\Users\LENOVO\.workbuddy\skills\image-knowledge-converter\
echo.
echo 提示: WorkBuddy 会自动识别新的 Skill
echo       重启 WorkBuddy 或刷新页面即可使用
echo.
pause
