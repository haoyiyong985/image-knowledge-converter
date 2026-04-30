@echo off
chcp 65001 >nul
echo 正在归档示范文件夹中的图片...

if not exist "d:\新建文件夹\已处理图片\示范" mkdir "d:\新建文件夹\已处理图片\示范"

xcopy "d:\新建文件夹\待处理图片\示范\*.*" "d:\新建文件夹\已处理图片\示范\" /E /I /Y

if %errorlevel% == 0 (
    echo 归档完成！
    echo 正在删除待处理文件夹中的图片...
    rmdir /S /Q "d:\新建文件夹\待处理图片\示范"
    mkdir "d:\新建文件夹\待处理图片\示范"
    echo 清理完成！
) else (
    echo 归档失败，请检查路径是否正确
)

pause