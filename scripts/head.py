try:
    with open('test_final.txt', 'r', encoding='utf-8') as f:
        content = f.read()
except:
    with open('test_final.txt', 'r', encoding='gbk', errors='replace') as f:
        content = f.read()

print('文件前20行:')
lines = content.split('\n')
for i, line in enumerate(lines[:20]):
    print(f'{i}: {repr(line[:100])}')
print(f'\n文件总行数: {len(lines)}')
