import json
with open('处理结果/处理报告.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('='*50)
print('测试完成报告')
print('='*50)
print(f"总计处理: {report['processed']}/{report['total_images']} 张")
print(f"总耗时: {report['elapsed_seconds']:.1f} 秒")
print()
print('分类统计:')
for cat, count in report['category_stats'].items():
    print(f'  - {cat}: {count} 张')
print()
print('IMA同步统计:')
ima_ok = [r for r in report['results'] if r.get('ima_id')]
print(f'  - 成功同步: {len(ima_ok)} 张')
print(f'  - 失败: {report["processed"] - len(ima_ok)} 张')
print()
if ima_ok:
    print('IMA同步的文档ID:')
    for r in ima_ok[:5]:
        print(f'  - {r["ima_id"]}: {r["image"][:40]}...')
    if len(ima_ok) > 5:
        print(f'  ... 还有 {len(ima_ok)-5} 个')
