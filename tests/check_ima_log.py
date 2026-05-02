#!/usr/bin/env python3
import json
from pathlib import Path

log_file = Path('处理结果/ima_sync_log.json')
if log_file.exists():
    data = json.loads(log_file.read_text(encoding='utf-8'))
    print('=== IMA 同步日志 ===')
    print(f'总记录数: {len(data)}')
    print()
    # 显示最新的5条
    items = list(data.items())[-5:]
    for key, value in items:
        print(f'文档: {value.get("title", key)}')
        print(f'  doc_id: {value.get("doc_id", "N/A")}')
        print(f'  first_sync: {value.get("first_sync", "N/A")}')
        print(f'  last_sync: {value.get("last_sync", "N/A")}')
        print()
else:
    print('日志文件不存在')
