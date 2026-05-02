#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装必要的 Python 依赖
"""

import subprocess
import sys


def install_package(package):
    """安装单个包"""
    print(f"安装 {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"  ✓ {package} 安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ✗ {package} 安装失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("安装依赖")
    print("=" * 60)
    print()
    
    # 必需的依赖
    required_packages = [
        "python-dotenv",      # 环境变量管理
        "requests",           # HTTP 请求
        "Pillow",             # 图像处理
        "pytesseract",        # Tesseract OCR
        "opencv-python",      # OpenCV 图像处理
        "numpy",              # 数值计算
        "PyYAML",             # YAML 解析
        "python-docx",        # Word 文档生成
        "markdown",           # Markdown 处理
    ]
    
    # 可选依赖
    optional_packages = [
        "keyring",            # 系统密钥管理（可选）
        "cryptography",       # 加密（可选）
    ]
    
    print("【必需依赖】")
    success_count = 0
    for package in required_packages:
        if install_package(package):
            success_count += 1
    
    print()
    print("【可选依赖】")
    for package in optional_packages:
        install_package(package)
    
    print()
    print("=" * 60)
    print(f"安装完成: {success_count}/{len(required_packages)} 个必需包")
    print("=" * 60)
    
    if success_count == len(required_packages):
        print()
        print("✓ 所有必需依赖已安装！")
        print()
        print("下一步:")
        print("  1. 运行配置向导: python setup_config.py")
        print("  2. 配置 API 密钥")
        return 0
    else:
        print()
        print("✗ 部分依赖安装失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
