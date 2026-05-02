#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置向导 - 帮助用户设置 API 密钥
"""

import os
import sys
from pathlib import Path


def setup_config():
    """交互式配置向导"""
    print("=" * 60)
    print("图片知识库整理工具 - 配置向导")
    print("=" * 60)
    print()
    print("本向导将帮助你配置 OCR 所需的 API 密钥")
    print("密钥将保存在 .env 文件中，不会上传到任何地方")
    print()
    
    config = {}
    
    # 腾讯云配置
    print("-" * 60)
    print("【腾讯云 OCR 配置】")
    print("-" * 60)
    print("获取地址: https://console.cloud.tencent.com/cam/capi")
    print("免费额度: 1000次/月")
    print()
    
    config['TENCENT_SECRET_ID'] = input("腾讯云 SecretId: ").strip()
    config['TENCENT_SECRET_KEY'] = input("腾讯云 SecretKey: ").strip()
    
    # 百度云配置
    print()
    print("-" * 60)
    print("【百度云 OCR 配置】")
    print("-" * 60)
    print("获取地址: https://console.bce.baidu.com/ai/")
    print("免费额度: 50000次/月")
    print()
    
    config['BAIDU_APP_ID'] = input("百度 AppId: ").strip()
    config['BAIDU_API_KEY'] = input("百度 API Key: ").strip()
    config['BAIDU_SECRET_KEY'] = input("百度 Secret Key: ").strip()
    
    # Tesseract 路径
    print()
    print("-" * 60)
    print("【Tesseract 路径配置（可选）】")
    print("-" * 60)
    print("如果 Tesseract 安装在非默认位置，请修改路径")
    print("默认: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
    print()
    
    tess_path = input("Tesseract 路径 (直接回车使用默认): ").strip()
    config['TESSERACT_PATH'] = tess_path if tess_path else r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    # 保存配置
    print()
    print("-" * 60)
    print("保存配置...")
    print("-" * 60)
    
    env_path = Path(__file__).parent / '.env'
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write("# 腾讯云 OCR 配置\n")
            f.write("# 获取地址: https://console.cloud.tencent.com/cam/capi\n")
            f.write(f"TENCENT_SECRET_ID={config['TENCENT_SECRET_ID']}\n")
            f.write(f"TENCENT_SECRET_KEY={config['TENCENT_SECRET_KEY']}\n")
            f.write("\n")
            f.write("# 百度云 OCR 配置\n")
            f.write("# 获取地址: https://console.bce.baidu.com/ai/\n")
            f.write(f"BAIDU_APP_ID={config['BAIDU_APP_ID']}\n")
            f.write(f"BAIDU_API_KEY={config['BAIDU_API_KEY']}\n")
            f.write(f"BAIDU_SECRET_KEY={config['BAIDU_SECRET_KEY']}\n")
            f.write("\n")
            f.write("# Tesseract 路径\n")
            f.write(f"TESSERACT_PATH={config['TESSERACT_PATH']}\n")
        
        print(f"[OK] 配置已保存到: {env_path}")
        print()
        print("=" * 60)
        print("配置完成！")
        print("=" * 60)
        print()
        print("你可以随时运行以下命令修改配置:")
        print("  python setup_config.py")
        print()
        print("或者手动编辑 .env 文件")
        print()
        
        # 显示配置摘要
        print("配置摘要:")
        if config['TENCENT_SECRET_ID']:
            print(f"  ✓ 腾讯云: {config['TENCENT_SECRET_ID'][:8]}...")
        else:
            print(f"  ✗ 腾讯云: 未配置")
        
        if config['BAIDU_APP_ID']:
            print(f"  ✓ 百度云: AppId {config['BAIDU_APP_ID']}")
        else:
            print(f"  ✗ 百度云: 未配置")
        
        print(f"  ✓ Tesseract: {config['TESSERACT_PATH']}")
        print()
        
        return True
        
    except Exception as e:
        print(f"[错误] 保存配置失败: {e}")
        return False


def check_existing_config():
    """检查是否已有配置"""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        print("=" * 60)
        print("检测到已有配置文件")
        print("=" * 60)
        print()
        print(f"配置文件: {env_path}")
        print()
        
        choice = input("是否重新配置? (y/N): ").strip().lower()
        
        if choice != 'y':
            print()
            print("保持现有配置，退出向导。")
            return False
    
    return True


def main():
    """主函数"""
    # 检查是否需要重新配置
    if not check_existing_config():
        return
    
    # 运行配置向导
    if setup_config():
        print()
        print("建议下一步操作:")
        print("  1. 测试配置: python check_baidu_ocr.py")
        print("  2. 测试 OCR: python config_ocr_env.py")
        print("  3. 开始处理: python auto_process.py")
    else:
        print()
        print("配置失败，请重试。")


if __name__ == "__main__":
    main()
