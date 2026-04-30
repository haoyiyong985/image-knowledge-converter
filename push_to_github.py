#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 推送脚本 - 图片转知识库系统
"""

import os
import subprocess
import sys
from pathlib import Path

def run_cmd(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    print(f"\n[执行] {cmd}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        if result.stdout:
            print(result.stdout)
        if result.stderr and result.returncode != 0:
            print(f"[警告] {result.stderr}", file=sys.stderr)
        if check and result.returncode != 0:
            print(f"[错误] 命令失败，返回码: {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"[错误] {e}")
        return False

def find_git():
    """查找 git 可执行文件"""
    # 常见安装路径
    possible_paths = [
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Git\bin\git.exe",
        r"C:\Users\LENOVO\AppData\Local\Programs\Git\bin\git.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 尝试从 PATH 查找
    try:
        result = subprocess.run(['where', 'git'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None

def main():
    project_dir = r"d:\新建文件夹"
    repo_url = "https://github.com/cuixiaohui985/image-knowledge-converter.git"
    
    print("=" * 50)
    print("  GitHub 推送脚本 - 图片转知识库系统")
    print("=" * 50)
    
    # 查找 git
    git_path = find_git()
    if not git_path:
        print("\n[错误] 未找到 Git！")
        print("请先安装 Git:")
        print("  下载地址: https://git-scm.com/download/win")
        print("  或: https://github.com/git-for-windows/git/releases")
        input("\n按回车键退出...")
        return 1
    
    print(f"\n[1/6] 找到 Git: {git_path}")
    
    # 进入项目目录
    os.chdir(project_dir)
    print(f"[2/6] 进入项目目录: {project_dir}")
    
    # 初始化仓库
    git_dir = Path(project_dir) / ".git"
    if not git_dir.exists():
        print("[3/6] 初始化 Git 仓库...")
        run_cmd(f'"{git_path}" init')
        run_cmd(f'"{git_path}" config user.email "user@local"')
        run_cmd(f'"{git_path}" config user.name "Local User"')
    else:
        print("[3/6] Git 仓库已存在，跳过初始化")
    
    # 添加远程仓库
    print("[4/6] 添加远程仓库...")
    run_cmd(f'"{git_path}" remote remove origin', check=False)
    run_cmd(f'"{git_path}" remote add origin {repo_url}')
    
    # 拉取现有内容
    print("[5/6] 拉取 GitHub 现有内容...")
    run_cmd(f'"{git_path}" pull origin master --allow-unrelated-histories', check=False)
    
    # 添加所有文件并提交
    print("[6/6] 提交并推送代码...")
    run_cmd(f'"{git_path}" add .')
    run_cmd(f'"{git_path}" commit -m "Initial commit: 导入图片转知识库系统"', check=False)
    
    # 推送到 GitHub
    print("\n" + "=" * 50)
    print("开始推送到 GitHub...")
    print("=" * 50)
    print("如果提示输入用户名密码:")
    print("  用户名: cuixiaohui985")
    print("  密码: 你的 GitHub 密码或 Personal Access Token")
    print("=" * 50 + "\n")
    
    success = run_cmd(f'"{git_path}" push -u origin master --force', check=False)
    
    print("\n" + "=" * 50)
    if success:
        print("  ✅ 推送成功！")
        print(f"  仓库地址: {repo_url}")
    else:
        print("  ❌ 推送失败，请检查错误信息")
    print("=" * 50)
    
    input("\n按回车键退出...")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
