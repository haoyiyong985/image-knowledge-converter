#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯云OCR测试脚本
检查配置并测试实际调用
"""

import json
import sys
from pathlib import Path

# 加载配置
BASE_DIR = Path("D:/新建文件夹")
CONFIG_FILE = BASE_DIR / "ocr_config.json"

def test_tencent_config():
    """测试腾讯云配置"""
    print("=" * 60)
    print("腾讯云OCR配置检查")
    print("=" * 60)
    
    if not CONFIG_FILE.exists():
        print("[ERROR] 配置文件不存在:", CONFIG_FILE)
        return False
    
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"[ERROR] 加载配置文件失败: {e}")
        return False
    
    tencent_config = config.get('tencent', {})
    secret_id = tencent_config.get('secret_id', '')
    secret_key = tencent_config.get('secret_key', '')
    
    # 检查SecretId
    if not secret_id:
        print("[ERROR] SecretId 未配置")
        return False
    
    if len(secret_id) < 20:
        print(f"[WARNING] SecretId 长度异常 ({len(secret_id)}字符)，正常应为30+字符")
    else:
        print(f"[OK] SecretId 已配置: {secret_id[:10]}...{secret_id[-4:]}")
    
    # 检查SecretKey
    if not secret_key:
        print("[ERROR] SecretKey 未配置")
        return False
    
    if len(secret_key) < 20:
        print(f"[WARNING] SecretKey 长度异常 ({len(secret_key)}字符)，正常应为30+字符")
    else:
        print(f"[OK] SecretKey 已配置: {secret_key[:10]}...{secret_key[-4:]}")
    
    return True

def test_tencent_api():
    """测试腾讯云API调用"""
    print("\n" + "=" * 60)
    print("腾讯云OCR API测试")
    print("=" * 60)
    
    # 查找测试图片
    test_dirs = [
        BASE_DIR / "已处理图片" / "示范",
        BASE_DIR / "已处理图片" / "游攻略",
    ]
    
    test_image = None
    for test_dir in test_dirs:
        if test_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                images = list(test_dir.glob(ext))
                if images:
                    test_image = images[0]
                    break
            if test_image:
                break
    
    if not test_image:
        print("[ERROR] 找不到测试图片")
        return False
    
    print(f"[INFO] 测试图片: {test_image.name}")
    
    # 尝试调用OCR
    try:
        from ocr_engine_manager import get_ocr_manager
        
        manager = get_ocr_manager()
        result, engine = manager.recognize_image(str(test_image))
        
        print(f"[INFO] 使用的引擎: {engine}")
        
        if result == "__AI_VISION__":
            print("[WARNING] 回退到AI视觉识别，云OCR可能配置有误")
            return False
        
        if result:
            print("[OK] OCR识别成功")
            print(f"[INFO] 识别结果前100字:\n{result[:100]}...")
            return True
        else:
            print("[ERROR] OCR返回空结果")
            return False
            
    except Exception as e:
        print(f"[ERROR] OCR调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("腾讯云OCR诊断工具")
    print("=" * 60)
    
    # 步骤1: 检查配置
    config_ok = test_tencent_config()
    
    if not config_ok:
        print("\n[ERROR] 配置检查失败，请检查 ocr_config.json")
        return 1
    
    # 步骤2: 测试API
    api_ok = test_tencent_api()
    
    print("\n" + "=" * 60)
    print("诊断结果")
    print("=" * 60)
    
    if api_ok:
        print("[OK] 腾讯云OCR工作正常")
        return 0
    else:
        print("[ERROR] 腾讯云OCR存在问题")
        print("\n可能的原因:")
        print("1. SecretId/SecretKey 不正确或已过期")
        print("2. 腾讯云账号未开通OCR服务")
        print("3. API密钥权限不足")
        print("4. 免费额度已用完")
        print("\n建议操作:")
        print("1. 登录 https://console.cloud.tencent.com/cam/capi 检查密钥")
        print("2. 登录 https://console.cloud.tencent.com/ocr 确认服务已开通")
        print("3. 检查密钥是否有OCR调用权限")
        return 1

if __name__ == "__main__":
    sys.exit(main())
