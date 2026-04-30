#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IMA API 调试脚本 - 检查完整的API响应"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env
load_dotenv()

client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')
base_url = 'https://ima.qq.com/openapi/note/v1'

print("=" * 60)
print("IMA API 调试脚本")
print("=" * 60)
print(f"ClientID: {client_id[:10]}... (长度: {len(client_id)})")
print(f"APIKey: {api_key[:10]}... (长度: {len(api_key)})")
print()

# 测试1: 验证凭证
print("[测试1] 验证凭证 (list_note_folder_by_cursor)...")
try:
    import requests
    headers = {
        'ima-openapi-clientid': client_id,
        'ima-openapi-apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/list_note_folder_by_cursor"
    payload = {"cursor": "0", "limit": 1}
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应头: {dict(response.headers)}")
    print(f"响应内容: {response.text[:500]}")
    
    try:
        result = response.json()
        print(f"\n解析后的JSON: {json.dumps(result, ensure_ascii=False, indent=2)[:1000]}")
    except:
        print("无法解析为JSON")
        
except Exception as e:
    print(f"请求失败: {e}")

print()
print("=" * 60)

# 测试2: 导入文档
print("[测试2] 导入文档测试 (import_doc)...")
try:
    headers = {
        'ima-openapi-clientid': client_id,
        'ima-openapi-apikey': api_key,
        'Content-Type': 'application/json'
    }
    
    url = f"{base_url}/import_doc"
    payload = {
        "content_format": 1,  # Markdown
        "content": "# 测试文档\n\n这是一个测试。"
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"状态码: {response.status_code}")
    print(f"响应内容: {response.text[:1000]}")
    
    try:
        result = response.json()
        print(f"\n解析后的JSON: {json.dumps(result, ensure_ascii=False, indent=2)[:2000]}")
        
        # 检查常用字段
        print(f"\n字段检查:")
        print(f"  - errcode: {result.get('errcode')}")
        print(f"  - retcode: {result.get('retcode')}")
        print(f"  - doc_id: {result.get('doc_id')}")
        print(f"  - data.doc_id: {result.get('data', {}).get('doc_id')}")
        print(f"  - errmsg: {result.get('errmsg')}")
        print(f"  - msg: {result.get('msg')}")
        print(f"  - code: {result.get('code')}")
        
    except:
        print("无法解析为JSON")
        
except Exception as e:
    print(f"请求失败: {e}")

print()
print("=" * 60)
print("调试完成")
