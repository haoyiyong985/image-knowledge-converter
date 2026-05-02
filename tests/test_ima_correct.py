# -*- coding: utf-8 -*-
"""
用正确的IMA API端点测试连接
"""
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')

BASE_URL = 'https://ima.qq.com/openapi/note/v1'

headers = {
    'ima-openapi-clientid': client_id,
    'ima-openapi-apikey': api_key,
    'Content-Type': 'application/json'
}

print(f'CLIENTID: {client_id}')
print(f'BASE_URL: {BASE_URL}')
print()

# 测试 import_doc 端点
print('=== 测试 import_doc 端点 ===')
test_payload = {
    'content_format': 1,
    'content': '# 连接测试\n\n> 这是一条自动测试笔记，可以删除\n\n**测试时间**: 2026-04-25\n\n---\n*连接验证*\n'
}

try:
    resp = requests.post(f'{BASE_URL}/import_doc', json=test_payload, headers=headers, timeout=15)
    print(f'HTTP {resp.status_code}')
    print(f'响应: {resp.text[:500]}')
    
    if resp.status_code == 200:
        data = resp.json()
        code = data.get('code', -1)
        print(f'code: {code}')
        if code == 0:
            note_id = data.get('data', {}).get('note_id', '')
            print(f'\n✅ IMA API 正常! 测试笔记 note_id: {note_id}')
        else:
            print(f'\n❌ API返回错误 code={code}: {data}')
    else:
        print(f'\n❌ HTTP错误')
except Exception as e:
    print(f'\n❌ 异常: {e}')
