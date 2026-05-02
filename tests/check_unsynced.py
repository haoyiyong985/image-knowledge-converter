# -*- coding: utf-8 -*-
"""检查未同步文档，并准备将新处理的文档同步到IMA"""
import json
from pathlib import Path

result_dir = Path('处理结果')
sync_log_file = result_dir / 'ima_sync_log.json'

# 加载同步日志
sync_log = json.loads(sync_log_file.read_text(encoding='utf-8'))
synced_hashes = set(sync_log.keys())

print('=== 检查处理结果里的所有知识文档 ===\n')

synced_docs = []
unsynced_docs = []

for md_file in sorted(result_dir.rglob('*.md')):
    if md_file.name.startswith('_') or md_file.name == 'README.md':
        continue
    content = md_file.read_text(encoding='utf-8')
    hash_val = None
    for line in content.split('\n'):
        if 'content_hash:' in line:
            hash_val = line.split('content_hash:')[-1].strip()
            break
    
    if hash_val is None:
        continue  # 跳过无hash的（系统报告）
    
    synced = hash_val in synced_hashes
    if synced:
        synced_docs.append({
            'file': md_file,
            'hash': hash_val,
            'title': sync_log[hash_val].get('title'),
            'last_sync': sync_log[hash_val].get('last_sync'),
        })
    else:
        # 提取标题
        title = md_file.stem
        for line in content.split('\n'):
            if line.startswith('# '):
                title = line[2:].strip()
                break
        unsynced_docs.append({
            'file': md_file,
            'hash': hash_val,
            'title': title,
        })

print(f'已同步文档: {len(synced_docs)} 个')
print(f'未同步文档: {len(unsynced_docs)} 个\n')

if unsynced_docs:
    print('=== 未同步文档列表 ===')
    for doc in unsynced_docs:
        print(f"  [{doc['file'].parent.name}] {doc['title']}")
        print(f"    文件: {doc['file'].name}")
        print(f"    hash: {doc['hash'][:16]}...")
        print()
else:
    print('✅ 所有知识文档均已同步！')

print('\n=== 最新同步（按时间排序最近5条）===')
recent = sorted(sync_log.items(), key=lambda x: x[1].get('last_sync', ''), reverse=True)[:5]
for k, v in recent:
    print(f"  {v.get('title')} - {v.get('last_sync', '')[:19]}")
