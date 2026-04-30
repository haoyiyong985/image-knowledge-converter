import sys
try:
    with open('test_final.txt', 'r', encoding='utf-8') as f:
        content = f.read()
except:
    with open('test_final.txt', 'r', encoding='gbk', errors='replace') as f:
        content = f.read()

lines = content.split('\n')
count = 0
for line in lines:
    if 'IMA' in line or '同步' in line or '处理完成' in line or '总计' in line:
        print(line)
        count += 1
print(f'\n共找到 {count} 条匹配')
