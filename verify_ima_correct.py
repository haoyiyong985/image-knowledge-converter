# -*- coding: utf-8 -*-
"""
用正确的IMA API域名和认证方式验证连接，并强制同步所有知识文档
"""
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import time

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
print(f'APIKEY前20位: {api_key[:20]}...')
print()

# Step 1: 测试连接
print('=== Step 1: 测试IMA API连接 ===')
try:
    test_payload = {
        'title': '__test__',
        'content': '# 测试\n测试连接'
    }
    resp = requests.post(f'{BASE_URL}/create', json=test_payload, headers=headers, timeout=15)
    print(f'HTTP 状态码: {resp.status_code}')
    print(f'响应: {resp.text[:500]}')
    
    if resp.status_code == 200:
        data = resp.json()
        ret = data.get('ret', -1)
        print(f'ret: {ret}')
        if ret == 0:
            note_id = data.get('data', {}).get('note_id', '')
            print(f'测试笔记创建成功，note_id: {note_id}')
            print('✅ IMA API 连接正常！')
        else:
            print(f'API返回错误: {data}')
    else:
        print('❌ 连接失败')
except Exception as e:
    print(f'异常: {e}')
    import sys
    sys.exit(1)

print()

# Step 2: 读取所有需要同步的文档
print('=== Step 2: 检查待同步文档 ===')
result_dir = Path('处理结果')
sync_log_file = result_dir / 'ima_sync_log.json'
sync_log = json.loads(sync_log_file.read_text(encoding='utf-8'))

# 收集所有有content_hash的文档
docs_to_check = []
for md_file in sorted(result_dir.rglob('*.md')):
    if md_file.name.startswith('_') or md_file.name == 'README.md':
        continue
    content = md_file.read_text(encoding='utf-8')
    hash_val = None
    for line in content.split('\n'):
        if 'content_hash:' in line:
            hash_val = line.split('content_hash:')[-1].strip()
            break
    if hash_val:
        docs_to_check.append({'file': md_file, 'hash': hash_val, 'content': content})

print(f'找到 {len(docs_to_check)} 个知识文档')

# 显示每个文档的同步状态
for doc in docs_to_check:
    synced = doc['hash'] in sync_log
    title = sync_log.get(doc['hash'], {}).get('title') or doc['file'].stem
    last_sync = sync_log.get(doc['hash'], {}).get('last_sync', '从未同步')[:19] if synced else '从未同步'
    status = '✅ 已同步' if synced else '❌ 未同步'
    print(f'  {status} | {title} | {last_sync}')
