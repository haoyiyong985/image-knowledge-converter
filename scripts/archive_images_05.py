# -*- coding: utf-8 -*-
"""
归档美食地图已处理图片
"""
import os
import shutil

SOURCE_DIR = r"D:\新建文件夹\待处理图片\美食地图"
TARGET_DIR = r"D:\新建文件夹\已处理图片\美食地图"

def archive_images():
    # 确保目标目录存在
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 获取所有图片文件
    image_files = []
    for filename in os.listdir(SOURCE_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            image_files.append(filename)
    
    if not image_files:
        print("No images to archive")
        return
    
    print(f"Found {len(image_files)} images to archive")
    
    # 移动文件
    moved_count = 0
    for filename in image_files:
        source_path = os.path.join(SOURCE_DIR, filename)
        target_path = os.path.join(TARGET_DIR, filename)
        
        try:
            shutil.move(source_path, target_path)
            moved_count += 1
            print(f"  Archived: {filename}")
        except Exception as e:
            print(f"  Failed: {filename} - {e}")
    
    print(f"\nArchive complete: {moved_count}/{len(image_files)} images")

if __name__ == "__main__":
    archive_images()
