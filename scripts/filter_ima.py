lines = open('test_final.txt', 'r', encoding='utf-8', errors='replace').readlines()
for line in lines:
    if 'IMA' in line or '处理完成' in line or '总计' in line or '同步' in line:
        print(line.strip())
