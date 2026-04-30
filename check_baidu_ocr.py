#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查百度 OCR 配置和可用性
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# 从环境变量读取配置
API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')


def get_access_token():
    """获取百度 OCR access_token"""
    if not API_KEY or not SECRET_KEY:
        print("[错误] API Key 或 Secret Key 未配置")
        print("       请在 .env 文件中设置 BAIDU_API_KEY 和 BAIDU_SECRET_KEY")
        return None
    
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    
    try:
        data = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'access_token' in result:
                return result['access_token']
            else:
                print(f"[错误] 获取 token 失败: {result.get('error_description', '未知错误')}")
                return None
                
    except Exception as e:
        print(f"[错误] 请求失败: {e}")
        return None


def check_ocr_api(access_token):
    """测试 OCR API 是否可用"""
    url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    
    # 使用一个简单的 base64 图片（1x1 像素的透明图）
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    try:
        data = urllib.parse.urlencode({'image': test_image}).encode('utf-8')
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'error_code' not in result:
                print("[OK] OCR API 可用")
                return True
            else:
                print(f"[错误] API 错误: {result.get('error_msg')}")
                return False
                
    except Exception as e:
        print(f"[错误] 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("百度 OCR 配置检查")
    print("=" * 60)
    
    # 检查配置
    print("\n[1] 检查配置...")
    if not API_KEY:
        print("  [FAIL] BAIDU_API_KEY 未设置")
        print("         请在 .env 文件中添加: BAIDU_API_KEY=你的APIKey")
        return False
    else:
        print(f"  [OK] API Key: {API_KEY[:8]}...")
    
    if not SECRET_KEY:
        print("  [FAIL] BAIDU_SECRET_KEY 未设置")
        print("         请在 .env 文件中添加: BAIDU_SECRET_KEY=你的SecretKey")
        return False
    else:
        print(f"  [OK] Secret Key: {SECRET_KEY[:8]}...")
    
    # 获取 token
    print("\n[2] 获取 Access Token...")
    access_token = get_access_token()
    if not access_token:
        return False
    print(f"  [OK] Token: {access_token[:20]}...")
    
    # 测试 API
    print("\n[3] 测试 OCR API...")
    if check_ocr_api(access_token):
        print("\n" + "=" * 60)
        print("[OK] 百度 OCR 配置正确，可以正常使用！")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("[FAIL] 百度 OCR 测试失败")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
