"""
IMA API 连接测试 + 手动同步脚本
测试 IMA OpenAPI 连接，并尝试同步新文档
"""
import requests
import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')
base_url = 'https://ima.qq.com/openapi/note/v1'

print('=== IMA API 测试 ===')
print(f'CLIENTID: {client_id}')
print(f'APIKEY: {api_key[:20]}...')
print()

headers = {
    'ima-openapi-clientid': client_id,
    'ima-openapi-apikey': api_key,
    'Content-Type': 'application/json'
}

# ————————————————————————————
# Step 1: 测试 API 连接（查笔记本列表）
# ————————————————————————————
print('Step 1: 测试 API 连接...')
try:
    resp = requests.post(
        f'{base_url}/list_doc',
        json={'page_size': 5, 'page': 1},
        headers=headers,
        timeout=15
    )
    print(f'  状态码: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'  ✅ API 连接正常！响应: {json.dumps(data, ensure_ascii=False)[:200]}')
    else:
        print(f'  响应: {resp.text[:400]}')
except Exception as e:
    print(f'  ❌ 异常: {e}')

print()

# ————————————————————————————
# Step 2: 测试导入笔记
# ————————————————————————————
print('Step 2: 测试导入一条测试笔记...')

test_content = f"""# 测试同步 - {datetime.now().strftime('%Y-%m-%d %H:%M')}

> 这是自动同步测试，请忽略此笔记

此笔记用于验证 IMA OpenAPI 连接是否正常。
"""

try:
    resp = requests.post(
        f'{base_url}/import_doc',
        json={
            'content_format': 1,  # 1=markdown
            'content': test_content
        },
        headers=headers,
        timeout=30
    )
    print(f'  状态码: {resp.status_code}')
    if resp.status_code == 200:
        data = resp.json()
        print(f'  ✅ 测试笔记创建成功！')
        print(f'  code: {data.get("code")}')
        print(f'  data: {json.dumps(data.get("data", {}), ensure_ascii=False)}')
        test_doc_id = data.get('data', {}).get('note_id')
        print(f'  note_id: {test_doc_id}')
    else:
        print(f'  ❌ 响应: {resp.text[:500]}')
except Exception as e:
    print(f'  ❌ 异常: {e}')

print()

# ————————————————————————————
# Step 3: 同步实际的新处理文档
# ————————————————————————————
print('Step 3: 查找需要同步的新文档...')

# 读取同步日志
sync_log_file = Path('处理结果/ima_sync_log.json')
sync_log = {}
if sync_log_file.exists():
    try:
        sync_log = json.loads(sync_log_file.read_text(encoding='utf-8'))
    except Exception:
        pass

# 获取已同步的 content_hash 列表
synced_hashes = set(sync_log.keys())
print(f'  已同步文档: {len(synced_hashes)} 条')

# 扫描处理结果中所有 .md 文档
result_dir = Path('处理结果')
md_files = list(result_dir.rglob('*.md'))
print(f'  总 Markdown 文档: {len(md_files)} 个')
print()

# 找出未同步的文档（解析 content_hash）
unsynced = []
for md_file in md_files:
    if md_file.name.startswith('_') or 'report' in md_file.name.lower():
        continue
    try:
        content = md_file.read_text(encoding='utf-8')
        # 提取 content_hash
        hash_match = None
        for line in content.split('\n'):
            if 'content_hash:' in line:
                hash_match = line.split('content_hash:')[-1].strip()
                break
        if hash_match and hash_match not in synced_hashes:
            # 提取标题和分类
            title = md_file.stem
            category = None
            for line in content.split('\n'):
                if '分类:' in line:
                    category = line.split('分类:')[-1].strip()
                    break
            unsynced.append({
                'file': md_file,
                'hash': hash_match,
                'title': title,
                'category': category,
                'content': content
            })
    except Exception as e:
        pass

print(f'  未同步文档: {len(unsynced)} 个')
if unsynced:
    for item in unsynced[:5]:
        print(f'    - {item["title"]} (hash: {item["hash"]})')

print()

if unsynced:
    print('Step 4: 尝试同步未同步文档...')
    success_count = 0
    for item in unsynced:
        title = item['title']
        content = item['content']
        category = item['category']
        hash_val = item['hash']

        full_content = f"# {title}\n\n"
        if category:
            full_content += f"> 分类: {category}\n"
        full_content += f"> 内容标识: {hash_val}\n\n"
        # 提取 CONTENT_START 后的内容
        if '<!-- CONTENT_START -->' in content:
            content_body = content.split('<!-- CONTENT_START -->')[-1].strip()
        else:
            content_body = content

        full_content += content_body + "\n\n---\n*自动同步自图片知识库*\n"

        try:
            resp = requests.post(
                f'{base_url}/import_doc',
                json={'content_format': 1, 'content': full_content},
                headers=headers,
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('code') == 0:
                    doc_id = data.get('data', {}).get('note_id', 'imported')
                    sync_log[hash_val] = {
                        'doc_id': doc_id,
                        'title': title,
                        'category': category,
                        'first_sync': datetime.now().isoformat(),
                        'last_sync': datetime.now().isoformat(),
                        'update_count': 1
                    }
                    success_count += 1
                    print(f'  ✅ 已同步: {title}  note_id={doc_id}')
                else:
                    print(f'  ❌ 失败: {title}  code={data.get("code")}  msg={data.get("msg")}')
            else:
                print(f'  ❌ 失败: {title}  HTTP {resp.status_code}')
        except Exception as e:
            print(f'  ❌ 异常: {title}  {e}')

    # 保存更新后的同步日志
    if success_count > 0:
        sync_log_file.write_text(json.dumps(sync_log, ensure_ascii=False, indent=2), encoding='utf-8')
        print()
        print(f'✅ 共成功同步 {success_count}/{len(unsynced)} 个文档，日志已更新')
    else:
        print('❌ 所有文档同步失败')
else:
    print('✅ 所有文档已同步，无需处理')
