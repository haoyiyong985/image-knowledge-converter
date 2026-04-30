#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从进度文件生成文档并同步到 ima
==============================
用途：将已处理但未生成文档的结果重新生成 .md 文件
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path("D:/新建文件夹")
RESULT_DIR = BASE_DIR / "处理结果"
PROGRESS_DIR = BASE_DIR / "progress"

# 分类体系
CATEGORIES = {
    "健康养生": {
        "doc_file": "01_抗炎饮食与营养科普.md"
    },
    "肠道健康": {
        "doc_file": "02_肠道健康与饮食分类.md"
    },
    "中医养生": {
        "doc_file": "03_中医养生与食疗.md"
    },
    "日常饮食": {
        "doc_file": "04_日常饮食建议.md"
    },
}


def generate_docs_from_progress(progress_file: Path):
    """从进度文件生成文档"""
    print(f"[INFO] 读取进度文件: {progress_file.name}")
    
    with open(progress_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    topic = data.get("topic", "未分类")
    results = data.get("results", [])
    
    # 按分类分组
    categorized = defaultdict(list)
    for result in results:
        if not result.get("success") or result.get("is_duplicate"):
            continue
        category = result.get("category", "新主题")
        categorized[category].append(result)
    
    generated_files = []
    
    # 为每个分类生成文档
    for category, items in categorized.items():
        # 确定文档文件名
        if category in CATEGORIES:
            doc_file = RESULT_DIR / CATEGORIES[category]["doc_file"]
            doc_title = f"{category}知识库"
        else:
            # 新主题：使用主题名作为文件名
            safe_topic = "".join(c for c in topic if c.isalnum() or c in "_-")
            doc_file = RESULT_DIR / f"06_{safe_topic}_新主题.md"
            doc_title = f"{topic} - 新主题知识库"
        
        # 生成内容
        content = f"\n## 批次处理 - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        content += f"**来源**: {topic} 主题\n\n"
        
        for result in items:
            content += f"### {result['image_name']}\n\n"
            content += f"**识别引擎**: {result.get('engine', '未知')} | "
            content += f"**置信度**: {result.get('confidence', 0):.2f}\n\n"
            # 使用引用格式而非代码块，避免在ima中显示为代码
            text_content = result['text'].strip()
            if text_content:
                # 将多行文本转换为引用格式
                lines = text_content.split('\n')
                quoted_lines = [f"> {line}" for line in lines if line.strip()]
                content += '\n'.join(quoted_lines) + '\n\n'
            else:
                content += '> （无识别内容）\n\n'
        
        # 追加到文档
        if doc_file.exists():
            with open(doc_file, 'a', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] 已追加到: {doc_file.name} ({len(items)} 条)")
        else:
            header = f"# {doc_title}\n\n"
            header += f"> 整理来源：图片识别自动归档\n"
            header += f"> 创建时间：{datetime.now().strftime('%Y-%m-%d')}\n\n"
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(header + content)
            print(f"[OK] 已创建: {doc_file.name} ({len(items)} 条)")
        
        generated_files.append(doc_file)
    
    return generated_files


def main():
    """主函数"""
    print("=" * 60)
    print("从进度文件生成文档")
    print("=" * 60)
    
    # 查找最新的进度文件
    progress_files = list(PROGRESS_DIR.glob("*.json"))
    if not progress_files:
        print("[ERROR] 未找到进度文件")
        return
    
    # 按修改时间排序，取最新的
    progress_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    all_generated = []
    for pf in progress_files[:3]:  # 处理最近3个
        files = generate_docs_from_progress(pf)
        all_generated.extend(files)
    
    if all_generated:
        print("\n" + "=" * 60)
        print("生成完成！")
        print("=" * 60)
        print("\n生成的文档:")
        for f in set(all_generated):
            print(f"  - {f.name}")
        print("\n现在可以运行: python ima_sync.py")
    else:
        print("\n[WARN] 没有生成任何文档")


if __name__ == "__main__":
    main()
