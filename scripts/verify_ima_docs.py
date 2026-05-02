# -*- coding: utf-8 -*-
"""验证IMA中已同步文档是否真实存在（通过get note_id接口）"""
import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')

headers = {
    'Authorization': f'Bearer {api_key}',
    'X-Client-ID': client_id,
    'Content-Type': 'application/json'
}

BASE_URL = 'https://imaapi.qq.com/ai/openapi/v1'

sync_log = json.loads(Path('处理结果/ima_sync_log.json').read_text(encoding='utf-8'))

# 按最近同步排序，取所有记录
items = sorted(sync_log.items(), key=lambda x: x[1].get('last_sync', ''), reverse=True)

print(f'=== 验证 IMA 中的文档（共 {len(items)} 条）===\n')

success_count = 0
fail_count = 0

for key, val in items[:20]:  # 最多验证20条
    title = val.get('title', '未知')
    note_id = val.get('doc_id', '')
    last_sync = val.get('last_sync', '')[:16]
    
    if not note_id:
        print(f'  [SKIP] {title} - 无note_id')
        continue
    
    # 尝试通过笔记ID查询
    try:
        url = f'{BASE_URL}/note/detail'
        resp = requests.post(url, json={'note_id': note_id}, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('error', {}).get('code') == 0 or data.get('ret') == 0:
                success_count += 1
                print(f'  [✅ 存在] {title} ({last_sync})')
            else:
                fail_count += 1
                err = data.get('error', {}).get('message') or data.get('msg', '')
                print(f'  [❓ 未知] {title} - {err}')
        elif resp.status_code == 404:
            fail_count += 1
            print(f'  [❌ 不存在] {title} - note_id: {note_id}')
        else:
            # 用创建接口返回的200判断，这里仅报告
            print(f'  [?] {title} - HTTP {resp.status_code}: {resp.text[:100]}')
    except Exception as e:
        print(f'  [ERR] {title}: {e}')

print(f'\n验证结果：成功 {success_count} / 失败 {fail_count}')

# 尝试另一种验证方式：search
print('\n=== 尝试 IMA 笔记列表接口 ===')
try:
    resp = requests.post(f'{BASE_URL}/note/list', json={'page': 1, 'page_size': 20}, headers=headers, timeout=10)
    print(f'HTTP {resp.status_code}')
    if resp.status_code == 200:
        print(resp.text[:500])
    else:
        print(resp.text[:300])
except Exception as e:
    print(f'异常: {e}')
