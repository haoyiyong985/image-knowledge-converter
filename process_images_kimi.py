#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Kimi-K2.5批量识别图片文字并分类整理
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 图片目录
IMAGE_DIR = Path("d:/新建文件夹/待处理图片/示范")
OUTPUT_DIR = Path("d:/新建文件夹/处理结果")
OUTPUT_DIR.mkdir(exist_ok=True)

# 定义分类体系
CATEGORIES = {
    "健康养生": {
        "keywords": ["健康", "养生", "医疗", "穴位", "中医", "食疗", "营养", "保健", "体检", "疾病", "治疗", "药品", "草药", "低密度脂蛋白", "清热解毒"],
        "description": "健康、养生、医疗相关内容"
    },
    "学习成长": {
        "keywords": ["学习", "读书", "知识", "技能", "成长", "教育", "培训", "课程", "书籍", "阅读", "微信读书"],
        "description": "学习资料、读书笔记、成长内容"
    },
    "生活记录": {
        "keywords": ["生活", "日常", "美食", "旅行", "购物", "娱乐", "休闲", "家庭"],
        "description": "日常生活、娱乐休闲内容"
    },
    "工作职场": {
        "keywords": ["工作", "职场", "办公", "管理", "项目", "会议", "报告", "业务"],
        "description": "工作相关、职场技能内容"
    },
    "科技数码": {
        "keywords": ["科技", "数码", "手机", "电脑", "软件", "APP", "互联网", "AI", "人工智能"],
        "description": "科技资讯、数码产品内容"
    },
    "其他": {
        "keywords": [],
        "description": "其他未分类内容"
    }
}


def get_all_images() -> List[Path]:
    """获取所有图片文件"""
    extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    images = []
    for ext in extensions:
        images.extend(IMAGE_DIR.glob(f"*{ext}"))
    return sorted(images)


def analyze_and_categorize(text_content: str, image_name: str) -> str:
    """
    分析内容并分类
    返回最匹配的分类名称
    """
    text_lower = text_content.lower()
    scores = {}
    
    for category, info in CATEGORIES.items():
        if category == "其他":
            continue
        score = 0
        for keyword in info["keywords"]:
            if keyword in text_content:
                score += 1
        scores[category] = score
    
    # 找到得分最高的分类
    if scores:
        best_category = max(scores.items(), key=lambda x: x[1])
        if best_category[1] > 0:
            return best_category[0]
    
    return "其他"


def process_batch_with_kimi(image_paths: List[Path], batch_num: int) -> List[Dict]:
    """
    使用Kimi处理一批图片
    由于无法直接调用Kimi API，这里生成处理模板供用户参考
    """
    results = []
    
    print(f"\n{'='*60}")
    print(f"批次 {batch_num} - 共 {len(image_paths)} 张图片")
    print(f"{'='*60}\n")
    
    for i, img_path in enumerate(image_paths, 1):
        print(f"\n图片 {i}/{len(image_paths)}: {img_path.name}")
        print(f"路径: {img_path}")
        print("-" * 40)
        
        # 这里记录需要处理的图片信息
        result = {
            "image_name": img_path.name,
            "image_path": str(img_path),
            "batch": batch_num,
            "index": i,
            "extracted_text": "",  # 将由Kimi填充
            "category": "",  # 将由Kimi或脚本填充
            "summary": ""  # 内容摘要
        }
        results.append(result)
    
    return results


def create_kimi_prompt_batch(image_paths: List[Path], batch_num: int) -> str:
    """
    为一批图片创建Kimi提示词
    """
    prompt = f"""请帮我识别以下{batch_num}张图片中的文字内容，并对每张图片进行分类。

## 分类体系：
1. **健康养生** - 健康、养生、医疗、穴位、中医、食疗、营养、保健、体检、疾病、治疗、药品等内容
2. **学习成长** - 学习资料、读书笔记、知识技能、教育培训、书籍阅读等内容
3. **生活记录** - 日常生活、美食、旅行、购物、娱乐休闲等内容
4. **工作职场** - 工作相关、职场技能、办公管理、项目会议等内容
5. **科技数码** - 科技资讯、数码产品、手机电脑、软件APP、AI人工智能等内容
6. **其他** - 不属于以上类别的内容

## 请按以下格式输出每张图片的结果：

"""
    
    for i, img_path in enumerate(image_paths, 1):
        prompt += f"""
### 图片{i}: {img_path.name}
- **提取的文字内容**：（请完整识别图片中的文字）
- **分类**：（从上述6个分类中选择最匹配的一个）
- **内容摘要**：（用1-2句话概括主要内容）
- **关键信息**：（提取重要的知识点或数据）

"""
    
    prompt += """
## 输出要求：
1. 尽可能完整准确地识别图片中的所有文字
2. 根据内容中心意思选择最恰当的分类
3. 如果图片包含多个主题，选择最主要的一个
4. 对于健康养生类内容，请特别注意提取具体的穴位名称、食疗方法、药品名称等关键信息

请开始处理这些图片。
"""
    
    return prompt


def save_batch_template(image_paths: List[Path], batch_num: int):
    """保存批处理模板"""
    prompt = create_kimi_prompt_batch(image_paths, batch_num)
    
    template_file = OUTPUT_DIR / f"batch_{batch_num:02d}_prompt.txt"
    with open(template_file, 'w', encoding='utf-8') as f:
        f.write(prompt)
    
    # 同时保存图片列表
    list_file = OUTPUT_DIR / f"batch_{batch_num:02d}_images.txt"
    with open(list_file, 'w', encoding='utf-8') as f:
        for i, img_path in enumerate(image_paths, 1):
            f.write(f"{i}. {img_path.name}\n")
            f.write(f"   路径: {img_path}\n\n")
    
    logger.info(f"批次 {batch_num} 模板已保存: {template_file}")
    return template_file


def main():
    """主函数"""
    print("="*60)
    print("图片转知识库 - Kimi批量处理工具")
    print("="*60)
    
    # 获取所有图片
    all_images = get_all_images()
    total_images = len(all_images)
    
    print(f"\n共发现 {total_images} 张图片")
    print(f"图片目录: {IMAGE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}\n")
    
    if total_images == 0:
        print("未找到图片文件！")
        return
    
    # 分批处理（每批5张，避免一次处理太多）
    batch_size = 5
    batches = [all_images[i:i+batch_size] for i in range(0, len(all_images), batch_size)]
    
    print(f"将分为 {len(batches)} 个批次处理，每批 {batch_size} 张图片\n")
    
    # 为每个批次创建模板
    for batch_num, batch_images in enumerate(batches, 1):
        save_batch_template(batch_images, batch_num)
    
    # 创建汇总文件
    summary_file = OUTPUT_DIR / "processing_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("图片处理汇总\n")
        f.write("="*60 + "\n\n")
        f.write(f"总图片数: {total_images}\n")
        f.write(f"批次数量: {len(batches)}\n")
        f.write(f"每批大小: {batch_size}\n\n")
        f.write("批次列表:\n")
        for i in range(1, len(batches)+1):
            f.write(f"  - 批次 {i:02d}: batch_{i:02d}_prompt.txt\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("使用说明:\n")
        f.write("="*60 + "\n\n")
        f.write("1. 打开每个批次的 prompt 文件 (batch_XX_prompt.txt)\n")
        f.write("2. 将文件内容复制到 Kimi 对话框\n")
        f.write("3. 同时上传该批次对应的图片文件\n")
        f.write("4. 让 Kimi 处理并返回结果\n")
        f.write("5. 将 Kimi 的回复保存到 batch_XX_result.txt\n")
        f.write("6. 所有批次处理完成后，运行 merge_results.py 合并结果\n")
        f.write("7. 最后运行 generate_word.py 生成 Word 文档\n")
    
    print(f"\n✓ 处理模板已生成！")
    print(f"✓ 汇总文件: {summary_file}")
    print(f"\n请查看 {OUTPUT_DIR} 目录中的文件，按说明使用 Kimi 处理图片。")
    
    # 显示前几个批次的图片
    print("\n" + "="*60)
    print("前3个批次的图片预览:")
    print("="*60)
    for batch_num, batch_images in enumerate(batches[:3], 1):
        print(f"\n批次 {batch_num}:")
        for i, img in enumerate(batch_images, 1):
            print(f"  {i}. {img.name}")


if __name__ == "__main__":
    main()
