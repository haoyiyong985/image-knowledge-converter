#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并Kimi处理结果并生成分类汇总
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

OUTPUT_DIR = Path("d:/新建文件夹/处理结果")


def parse_kimi_result(text: str) -> list:
    """
    解析Kimi返回的结果文本
    提取每张图片的信息
    """
    results = []
    
    # 按图片分割（匹配 "### 图片X:" 或 "图片X:" 格式）
    pattern = r'(?:###\s*)?图片\s*(\d+)[:：]\s*(.+?)(?=(?:###\s*)?图片\s*\d+[:：]|$)'
    matches = re.findall(pattern, text, re.DOTALL)
    
    for match in matches:
        img_num = match[0]
        content = match[1]
        
        # 提取各项信息
        result = {
            "image_num": int(img_num),
            "image_name": "",
            "extracted_text": "",
            "category": "其他",
            "summary": "",
            "key_info": ""
        }
        
        # 提取图片名称
        name_match = re.search(r'^(.+?)(?:\n|$)', content.strip())
        if name_match:
            result["image_name"] = name_match.group(1).strip()
        
        # 提取文字内容
        text_match = re.search(r'[提取的文字内容|内容|文字][：:]\s*\n?(.+?)(?=\n[-\*]|分类[：:]|$)', content, re.DOTALL)
        if text_match:
            result["extracted_text"] = text_match.group(1).strip()
        
        # 提取分类
        cat_match = re.search(r'分类[：:]\s*(.+?)(?:\n|$)', content)
        if cat_match:
            cat = cat_match.group(1).strip()
            # 标准化分类名称
            cat_mapping = {
                "健康养生": "健康养生",
                "健康": "健康养生",
                "养生": "健康养生",
                "医疗": "健康养生",
                "学习成长": "学习成长",
                "学习": "学习成长",
                "读书": "学习成长",
                "教育": "学习成长",
                "生活记录": "生活记录",
                "生活": "生活记录",
                "日常": "生活记录",
                "工作职场": "工作职场",
                "工作": "工作职场",
                "职场": "工作职场",
                "科技数码": "科技数码",
                "科技": "科技数码",
                "数码": "科技数码",
                "其他": "其他"
            }
            result["category"] = cat_mapping.get(cat, cat)
        
        # 提取摘要
        summary_match = re.search(r'内容摘要[：:]\s*(.+?)(?:\n|$)', content)
        if summary_match:
            result["summary"] = summary_match.group(1).strip()
        
        # 提取关键信息
        key_match = re.search(r'关键信息[：:]\s*(.+?)(?:\n|$)', content, re.DOTALL)
        if key_match:
            result["key_info"] = key_match.group(1).strip()
        
        results.append(result)
    
    return results


def load_all_results() -> dict:
    """
    加载所有批次的结果文件
    """
    all_results = []
    
    # 查找所有结果文件
    result_files = sorted(OUTPUT_DIR.glob("batch_*_result.txt"))
    
    if not result_files:
        print("未找到结果文件！请先将Kimi的处理结果保存为 batch_XX_result.txt")
        return {}
    
    print(f"找到 {len(result_files)} 个结果文件")
    
    for result_file in result_files:
        print(f"\n处理: {result_file.name}")
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        batch_results = parse_kimi_result(content)
        print(f"  解析到 {len(batch_results)} 条记录")
        all_results.extend(batch_results)
    
    # 按分类分组
    categorized = defaultdict(list)
    for result in all_results:
        category = result.get("category", "其他")
        categorized[category].append(result)
    
    return dict(categorized)


def save_categorized_results(categorized: dict):
    """
    保存分类后的结果
    """
    # 保存为JSON
    json_file = OUTPUT_DIR / "categorized_results.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(categorized, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 分类结果已保存: {json_file}")
    
    # 保存为文本报告
    report_file = OUTPUT_DIR / "分类汇总报告.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("图片内容分类汇总报告\n")
        f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*60 + "\n\n")
        
        # 统计信息
        total = sum(len(items) for items in categorized.values())
        f.write(f"总计处理: {total} 张图片\n")
        f.write(f"分类数量: {len(categorized)} 个\n\n")
        
        f.write("分类统计:\n")
        f.write("-"*60 + "\n")
        for category, items in sorted(categorized.items()):
            f.write(f"{category}: {len(items)} 张\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("详细内容\n")
        f.write("="*60 + "\n\n")
        
        # 详细内容
        for category, items in sorted(categorized.items()):
            f.write(f"\n{'='*60}\n")
            f.write(f"【{category}】({len(items)} 张)\n")
            f.write(f"{'='*60}\n\n")
            
            for i, item in enumerate(items, 1):
                f.write(f"{i}. {item.get('image_name', '未知')}\n")
                f.write(f"   摘要: {item.get('summary', '无')}\n")
                if item.get('key_info'):
                    f.write(f"   关键信息: {item.get('key_info')}\n")
                f.write("\n")
    
    print(f"✓ 汇总报告已保存: {report_file}")
    
    # 打印统计
    print("\n" + "="*60)
    print("分类统计:")
    print("="*60)
    for category, items in sorted(categorized.items()):
        print(f"  {category}: {len(items)} 张")


def main():
    """主函数"""
    print("="*60)
    print("合并Kimi处理结果")
    print("="*60)
    
    categorized = load_all_results()
    
    if categorized:
        save_categorized_results(categorized)
        print("\n✓ 处理完成！")
        print("\n下一步:")
        print("  运行: python generate_word.py")
        print("  生成Word文档")
    else:
        print("\n✗ 没有可处理的结果")


if __name__ == "__main__":
    main()
