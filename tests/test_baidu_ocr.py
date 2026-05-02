#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度云OCR诊断测试
"""

import os
import sys
import json
import urllib.request
import urllib.parse
from pathlib import Path
import base64

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        print(f"[INFO] 已加载 .env 文件")
    else:
        print(f"[WARN] .env 文件不存在")
except ImportError as e:
    print(f"[WARN] 无法加载 dotenv: {e}")

# 从环境变量读取配置
API_KEY = os.getenv('BAIDU_API_KEY', '')
SECRET_KEY = os.getenv('BAIDU_SECRET_KEY', '')

def test_baidu_ocr():
    """测试百度云OCR"""
    print("=" * 60)
    print("百度云OCR诊断测试")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n[1] 检查配置...")
    if not API_KEY:
        print("  [FAIL] BAIDU_API_KEY 未设置")
        return False
    else:
        print(f"  [OK] API Key: {API_KEY[:8]}...")
    
    if not SECRET_KEY:
        print("  [FAIL] BAIDU_SECRET_KEY 未设置")
        return False
    else:
        print(f"  [OK] Secret Key: {SECRET_KEY[:8]}...")
    
    # 2. 获取 Access Token
    print("\n[2] 获取 Access Token...")
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
                access_token = result['access_token']
                print(f"  [OK] Token 获取成功: {access_token[:20]}...")
                
                # 显示权限范围
                scope = result.get('scope', '')
                print(f"\n  [INFO] 权限范围: {scope}")
                
                if 'vis-ocr_通用文字识别' in scope or 'ocr_general' in scope:
                    print("  [OK] 包含通用文字识别权限")
                else:
                    print("  [WARN] 不包含通用文字识别权限")
                    print("         需要在百度云控制台开通此服务")
            else:
                print(f"  [FAIL] 获取 token 失败: {result}")
                return False
                
    except Exception as e:
        print(f"  [FAIL] 请求失败: {e}")
        return False
    
    # 3. 测试 OCR API
    print("\n[3] 测试 OCR API...")
    ocr_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
    
    # 使用一个简单的 base64 图片（1x1 像素的透明图）
    test_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    try:
        data = urllib.parse.urlencode({'image': test_image}).encode('utf-8')
        req = urllib.request.Request(ocr_url, data=data, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            if 'error_code' not in result:
                print("  [OK] OCR API 调用成功")
                print(f"\n  响应: {json.dumps(result, ensure_ascii=False, indent=2)[:200]}")
                return True
            else:
                error_code = result.get('error_code')
                error_msg = result.get('error_msg', '未知错误')
                print(f"  [FAIL] API 错误: {error_code} - {error_msg}")
                
                if error_code == 6:
                    print("\n  [诊断] 错误码6表示没有权限访问数据")
                    print("  [解决] 请在百度云控制台开通'通用文字识别'服务:")
                    print("         https://console.bce.baidu.com/ai/")
                
                return False
                
    except Exception as e:
        print(f"  [FAIL] 测试失败: {e}")
        return False

if __name__ == "__main__":
    success = test_baidu_ocr()
    
    print("\n" + "=" * 60)
    if success:
        print("[OK] 百度云OCR配置正确，可以正常使用！")
    else:
        print("[FAIL] 百度云OCR测试失败，请检查配置")
    print("=" * 60)
    
    sys.exit(0 if success else 1)
