# -*- coding: utf-8 -*-
import json
from pathlib import Path

sync_log = json.loads(Path('处理结果/ima_sync_log.json').read_text(encoding='utf-8'))

# 按 last_sync 排序，显示最近10条
items = sorted(sync_log.items(), key=lambda x: x[1].get('last_sync', ''), reverse=True)
print('=== 最近同步的10条文档 ===')
for key, val in items[:10]:
    print(f"  标题: {val.get('title')}")
    print(f"  note_id: {val.get('doc_id')}")
    print(f"  同步时间: {val.get('last_sync')}")
    print(f"  更新次数: {val.get('update_count')}")
    print()

print(f"\n=== 同步日志总共 {len(sync_log)} 条 ===")
