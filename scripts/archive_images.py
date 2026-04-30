# -*- coding: utf-8 -*-
"""
归档已处理图片
"""
import os
import shutil

SOURCE_DIR = r"D:\新建文件夹\待处理图片\示范"
TARGET_DIR = r"D:\新建文件夹\已处理图片\示范"

def archive_images():
    # 确保目标目录存在
    os.makedirs(TARGET_DIR, exist_ok=True)
    
    # 获取所有图片文件
    image_files = []
    for filename in os.listdir(SOURCE_DIR):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            image_files.append(filename)
    
    if not image_files:
        print("没有需要归档的图片")
        return
    
    print(f"发现 {len(image_files)} 张图片需要归档")
    
    # 移动文件
    moved_count = 0
    for filename in image_files:
        source_path = os.path.join(SOURCE_DIR, filename)
        target_path = os.path.join(TARGET_DIR, filename)
        
        try:
            shutil.move(source_path, target_path)
            moved_count += 1
            print(f"  已归档: {filename}")
        except Exception as e:
            print(f"  失败: {filename} - {e}")
    
    print(f"\n归档完成: {moved_count}/{len(image_files)} 张图片")

if __name__ == "__main__":
    archive_images()
