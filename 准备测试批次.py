#!/usr/bin/env python3
"""
准备测试批次 - 选择10张图片进行验证
"""
import shutil
from pathlib import Path
from datetime import datetime

def prepare_test_batch():
    """从已处理图片中选择10张移回待处理目录进行测试"""
    
    processed_dir = Path("D:/新建文件夹/已处理图片/示范")
    pending_dir = Path("D:/新建文件夹/待处理图片/示范")
    test_backup_dir = Path("D:/新建文件夹/已处理图片/示范_test_backup")
    
    # 确保目录存在
    pending_dir.mkdir(parents=True, exist_ok=True)
    test_backup_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取所有图片文件
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    all_images = []
    for ext in image_exts:
        all_images.extend(processed_dir.glob(f"*{ext}"))
    
    if not all_images:
        print("❌ 已处理图片目录中没有图片")
        return False
    
    # 选择前10张图片
    test_images = all_images[:10]
    
    print(f"📋 准备将以下 {len(test_images)} 张图片移回待处理目录进行测试：\n")
    
    moved_count = 0
    for i, img_path in enumerate(test_images, 1):
        # 移动到待处理目录
        pending_path = pending_dir / img_path.name
        backup_path = test_backup_dir / img_path.name
        
        # 如果待处理目录已存在同名文件，先备份
        if pending_path.exists():
            shutil.move(str(pending_path), str(backup_path))
            print(f"  {i}. {img_path.name} (已存在，已备份)")
        else:
            print(f"  {i}. {img_path.name}")
        
        # 从已处理目录移回待处理目录
        shutil.copy2(str(img_path), str(pending_path))
        moved_count += 1
    
    print(f"\n✅ 成功准备 {moved_count} 张测试图片")
    print(f"\n📂 图片位置: {pending_dir}")
    print(f"\n💡 下一步: 在 WorkBuddy 中发送「处理新图片」")
    
    return True

if __name__ == "__main__":
    prepare_test_batch()
