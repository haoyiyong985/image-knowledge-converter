import json
with open('处理结果/处理报告.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('检查 ima_id 字段:')
for r in report['results'][:3]:
    print(f"  image: {r['image'][:50]}")
    print(f"  ima_id: '{r.get('ima_id')}'")
    print(f"  ima_id type: {type(r.get('ima_id'))}")
    print()
