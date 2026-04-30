#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 环境配置脚本
从 .env 文件加载配置并设置环境变量
"""

import os
import sys
from pathlib import Path

# ============================================================
# 加载环境变量配置
# ============================================================
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[OK] 已加载配置文件: {env_path}")
    else:
        print(f"[WARN] 配置文件不存在: {env_path}")
        print("       请复制 .env.example 为 .env 并填入你的 API 密钥")
except ImportError:
    print("[WARN] 未安装 python-dotenv，请运行: pip install python-dotenv")

# ============================================================
# 从环境变量读取配置
# ============================================================
TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', '')
TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', '')
BAIDU_APP_ID = os.getenv('BAIDU_APP_ID', '')
BAIDU_API_KEY = os.getenv('BAIDU_API_KEY', '')
BAIDU_SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')
TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')


def setup_environment():
    """设置环境变量"""
    # 腾讯云
    if TENCENT_SECRET_ID:
        os.environ['TENCENT_SECRET_ID'] = TENCENT_SECRET_ID
    if TENCENT_SECRET_KEY:
        os.environ['TENCENT_SECRET_KEY'] = TENCENT_SECRET_KEY
    
    # 百度
    if BAIDU_APP_ID:
        os.environ['BAIDU_APP_ID'] = BAIDU_APP_ID
    if BAIDU_API_KEY:
        os.environ['BAIDU_API_KEY'] = BAIDU_API_KEY
    if BAIDU_SECRET_KEY:
        os.environ['BAIDU_SECRET_KEY'] = BAIDU_SECRET_KEY
    
    # Tesseract
    if os.path.exists(TESSERACT_PATH):
        os.environ['TESSERACT_CMD'] = TESSERACT_PATH
    
    print("=" * 60)
    print("OCR 环境变量配置完成")
    print("=" * 60)
    if TENCENT_SECRET_ID:
        print(f"[OK] 腾讯云 SecretId: {TENCENT_SECRET_ID[:8]}...")
    else:
        print("[WARN] 腾讯云 SecretId 未配置")
    if BAIDU_APP_ID:
        print(f"[OK] 百度 AppID: {BAIDU_APP_ID}")
    else:
        print("[WARN] 百度 AppID 未配置")
    print(f"[OK] Tesseract: {TESSERACT_PATH}")


def test_ocr():
    """测试 OCR 配置"""
    setup_environment()
    
    print("\n" + "=" * 60)
    print("测试 OCR 引擎")
    print("=" * 60)
    
    # 导入并测试
    try:
        from ocr_manager import OCRManager, OCREngine
        
        manager = OCRManager()
        
        print("\n引擎状态:")
        for engine in OCREngine:
            status = manager.engine_status[engine]
            icon = "[OK]" if status["available"] else "[FAIL]"
            print(f"  {icon} {engine.value}: {status['message']}")
        
        # 尝试自动选择
        engine = manager.auto_select_engine()
        if engine:
            print(f"\n[OK] 自动选择引擎: {engine.value}")
            return True
        else:
            print("\n[FAIL] 没有可用的 OCR 引擎")
            return False
            
    except Exception as e:
        print(f"\n[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_ocr()
