#!/usr/bin/env python3
"""测试 IMA API 是否正常工作"""
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')
base_url = 'https://ima.qq.com/openapi/note/v1'

print('=== IMA API 测试 ===')
print(f'CLIENTID: {client_id[:20]}...' if client_id else '未配置')
print(f'APIKEY: {api_key[:20]}...' if api_key else '未配置')
print()

# 测试获取笔记本列表
print('测试1: 获取笔记本列表...')
try:
    headers = {
        'ima-openapi-clientid': client_id,
        'ima-openapi-apikey': api_key,
        'Content-Type': 'application/json'
    }
    response = requests.post(
        f"{base_url}/get_notebook_list",
        json={},
        headers=headers,
        timeout=30
    )
    print(f'状态码: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'响应: {data}')
        if data.get('code') == 0:
            print('API 正常')
        else:
            print(f'API 错误: {data.get("msg")}')
    else:
        print(f'HTTP 错误: {response.text[:500]}')
except Exception as e:
    print(f'异常: {e}')
