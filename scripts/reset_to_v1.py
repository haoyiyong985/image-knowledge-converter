#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置到 1.0 版本状态
==================
1. 备份当前处理结果
2. 删除所有 .md 文档（保留备份）
3. 将图片移回待处理目录
4. 清理进度文件
"""

import shutil
import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path("D:/新建文件夹")
RESULT_DIR = BASE_DIR / "处理结果"
PENDING_DIR = BASE_DIR / "待处理图片"
PROCESSED_DIR = BASE_DIR / "已处理图片"
PROGRESS_DIR = BASE_DIR / "progress"

def backup_and_reset():
    """备份并重置"""
    print("=" * 60)
    print("重置到 1.0 版本状态")
    print("=" * 60)
    
    # 步骤 1: 创建备份
    backup_dir = BASE_DIR / f"backup_before_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"\n[步骤 1] 备份当前文档到: {backup_dir.name}")
    md_files = list(RESULT_DIR.glob("*.md"))
    for md_file in md_files:
        shutil.copy2(md_file, backup_dir)
    print(f"  [OK] 备份了 {len(md_files)} 个文档")
    
    # 步骤 2: 删除处理结果中的 .md 文件
    print(f"\n[步骤 2] 删除处理结果中的文档...")
    deleted = 0
    for md_file in RESULT_DIR.glob("*.md"):
        md_file.unlink()
        deleted += 1
    print(f"  [OK] 删除了 {deleted} 个文档")
    
    # 步骤 3: 将图片移回待处理目录
    print(f"\n[步骤 3] 将图片移回待处理目录...")
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    moved_count = 0
    
    for topic_dir in PROCESSED_DIR.iterdir():
        if topic_dir.is_dir():
            pending_topic_dir = PENDING_DIR / topic_dir.name
            pending_topic_dir.mkdir(parents=True, exist_ok=True)
            
            for ext in image_exts:
                for img in topic_dir.rglob(f'*{ext}'):
                    dst = pending_topic_dir / img.name
                    if not dst.exists():
                        shutil.move(str(img), str(dst))
                        moved_count += 1
    
    print(f"  [OK] 移回了 {moved_count} 张图片")
    
    # 步骤 4: 清理进度文件
    print(f"\n[步骤 4] 清理进度文件...")
    progress_count = 0
    for pf in PROGRESS_DIR.glob("*.json"):
        pf.unlink()
        progress_count += 1
    print(f"  [OK] 删除了 {progress_count} 个进度文件")
    
    # 完成
    print("\n" + "=" * 60)
    print("重置完成！")
    print("=" * 60)
    print(f"\n备份位置: {backup_dir}")
    print("\n现在可以使用 1.0 版本 workflow:")
    print("  1. python auto_process.py")
    print("  2. 在 WorkBuddy 中发送「处理新图片」")
    print("\nAI 会自动：识别 -> 整理 -> 分类 -> 生成文档")

if __name__ == "__main__":
    backup_and_reset()
