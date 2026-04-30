# -*- coding: utf-8 -*-
from pathlib import Path

pending_root = Path('待处理图片')
print('=== 待处理图片文件夹内容 ===\n')
total = 0
for folder in sorted(pending_root.iterdir()):
    if folder.is_dir():
        imgs = list(folder.glob('*'))
        imgs = [f for f in imgs if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']]
        print(f'  [{folder.name}] {len(imgs)} 张图片')
        for img in imgs[:5]:
            print(f'    - {img.name}')
        if len(imgs) > 5:
            print(f'    ... 还有 {len(imgs)-5} 张')
        total += len(imgs)
    elif folder.is_file():
        if folder.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']:
            print(f'  [根目录] {folder.name}')
            total += 1

print(f'\n总计: {total} 张待处理图片')
