#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 推送脚本 - 图片转知识库系统
一键配置 + 手动推送指导
"""

import os
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    print(f"  [执行] {cmd}")
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
            print(result.stdout.strip())
        if result.stderr and result.returncode != 0:
            print(f"  [警告] {result.stderr.strip()}", file=sys.stderr)
        if check and result.returncode != 0:
            return False
        return True
    except Exception as e:
        print(f"  [错误] {e}")
        return False


def find_git():
    """查找 git 可执行文件"""
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

    print("=" * 60)
    print("  GitHub 推送脚本 - 图片转知识库系统")
    print("=" * 60)

    # 查找 git
    git_path = find_git()
    if not git_path:
        print("\n[错误] 未找到 Git！")
        print("\n请先安装 Git:")
        print("  1. 打开浏览器访问: https://git-scm.com/download/win")
        print("  2. 下载并安装 Git for Windows")
        print("  3. 安装时选择默认选项即可")
        input("\n按回车键退出...")
        return 1

    print(f"\n[OK] 找到 Git: {git_path}")

    # 进入项目目录
    os.chdir(project_dir)
    print(f"[OK] 项目目录: {project_dir}")

    # 初始化仓库
    git_dir = Path(project_dir) / ".git"
    if not git_dir.exists():
        print("\n[1/5] 初始化 Git 仓库...")
        run_cmd(f'"{git_path}" init')
        run_cmd(f'"{git_path}" config user.email "user@local"')
        run_cmd(f'"{git_path}" config user.name "Local User"')
    else:
        print("\n[1/5] Git 仓库已存在，跳过初始化")

    # 添加远程仓库
    print("\n[2/5] 配置远程仓库...")
    run_cmd(f'"{git_path}" remote remove origin', check=False)
    run_cmd(f'"{git_path}" remote add origin {repo_url}')

    # 拉取现有内容
    print("\n[3/5] 同步 GitHub 内容...")
    run_cmd(f'"{git_path}" pull origin master --allow-unrelated-histories', check=False)

    # 排除嵌入仓库
    print("\n[4/5] 清理配置文件...")
    if Path(project_dir, "image-knowledge-converter").exists():
        run_cmd(f'"{git_path}" rm -r --cached image-knowledge-converter', check=False)
        print("  [已排除] image-knowledge-converter 嵌入仓库")

    # 添加所有文件并提交
    print("\n[5/5] 提交代码...")
    run_cmd(f'"{git_path}" add .')
    commit_result = run_cmd(
        f'"{git_path}" commit -m "Update: 同步图片转知识库系统代码"',
        check=False
    )

    if not commit_result:
        print("  [跳过] 没有新内容需要提交")

    # 显示推送命令
    print("\n" + "=" * 60)
    print("  配置完成！")
    print("=" * 60)
    print(f"\n仓库地址: {repo_url}\n")
    print("推送命令:")
    print("-" * 60)
    print(f'  cd /d "d:\\新建文件夹"')
    print(f'  "{git_path}" push -u origin master')
    print("-" * 60)
    print("\n如果你想一键推送，请:")
    print("  1. 复制上面两条命令")
    print("  2. 打开 CMD: 按 Win+R，输入 cmd，回车")
    print("  3. 粘贴并执行")
    print("\n推送时可能需要登录 GitHub:")
    print("  用户名: cuixiaohui985")
    print("  密码: GitHub Personal Access Token")
    print("  (不是登录密码，请到 GitHub 设置生成)")
    print("=" * 60)

    # 尝试自动推送
    print("\n正在尝试自动推送...")
    print("(如果失败请手动执行上面的命令)\n")

    success = run_cmd(f'"{git_path}" push -u origin master', check=False)

    if success:
        print("\n" + "=" * 60)
        print("  ✅ 推送成功！")
        print("=" * 60)
        print(f"\n请访问: {repo_url}")
    else:
        print("\n" + "=" * 60)
        print("  ⚠️ 自动推送失败")
        print("  请手动复制上面的推送命令执行")
        print("=" * 60)

    input("\n按回车键退出...")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
