#!/usr/bin/env python3
"""
自动处理批次图片 - 识别、整理、分类、生成文档
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from ocr_manager import OCRManager, OCREngine

def process_batch():
    """自动处理待处理目录中的所有图片"""
    
    pending_dir = Path("D:/新建文件夹/待处理图片/示范")
    result_dir = Path("D:/新建文件夹/处理结果")
    processed_dir = Path("D:/新建文件夹/已处理图片/示范")
    
    # 确保目录存在
    result_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)
    
    # 获取所有图片
    image_exts = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    images = []
    for ext in image_exts:
        images.extend(pending_dir.glob(f"*{ext}"))
    
    if not images:
        print("❌ 待处理目录中没有图片")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 开始自动处理 {len(images)} 张图片")
    print(f"{'='*60}\n")
    
    # 初始化 OCR 管理器
    ocr_manager = OCRManager()
    
    # 选择最佳引擎
    engine = ocr_manager.auto_select_engine()
    print(f"📷 使用识别引擎: {engine.value}\n")
    
    # 处理每张图片
    results = []
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] 处理: {img_path.name}")
        
        try:
            # 识别图片
            result = ocr_manager.recognize_image(str(img_path), engine)
            
            if result['success']:
                text = result.get('text', '')
                confidence = result.get('confidence', 0)
                
                print(f"    ✓ 识别成功 (置信度: {confidence:.2f})")
                print(f"    📝 内容预览: {text[:50]}...")
                
                results.append({
                    'image_name': img_path.name,
                    'text': text,
                    'confidence': confidence,
                    'engine': engine.value
                })
            else:
                print(f"    ✗ 识别失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"    ✗ 处理异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 识别完成: {len(results)}/{len(images)} 张成功")
    print(f"{'='*60}\n")
    
    if results:
        # 保存原始识别结果
        save_raw_results(results, result_dir)
        
        # 移动图片到已处理目录
        print("📂 归档图片...")
        for img_path in images:
            dest = processed_dir / img_path.name
            if dest.exists():
                dest.unlink()
            os.rename(str(img_path), str(dest))
        print(f"    ✓ 已归档 {len(images)} 张图片\n")
        
        print("✅ 处理完成！")
        print(f"📄 识别结果已保存到: {result_dir}/raw_recognition_results.txt")
        print(f"\n💡 下一步: 在 WorkBuddy 中发送「整理识别结果」进行内容整理和分类")
    
    return results

def save_raw_results(results, result_dir):
    """保存原始识别结果"""
    output_file = result_dir / "raw_recognition_results.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# 图片识别结果\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"图片数量: {len(results)}\n")
        f.write(f"{'='*60}\n\n")
        
        for i, result in enumerate(results, 1):
            f.write(f"## [{i}] {result['image_name']}\n")
            f.write(f"引擎: {result['engine']} | 置信度: {result['confidence']:.2f}\n\n")
            f.write(f"{result['text']}\n")
            f.write(f"\n{'-'*60}\n\n")
    
    print(f"📄 原始识别结果已保存: {output_file}\n")

if __name__ == "__main__":
    process_batch()
