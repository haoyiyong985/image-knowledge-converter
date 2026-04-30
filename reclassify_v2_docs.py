#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2文档AI重分类脚本

将V2的49个文档按V7原则重新分类：
1. AI分析文档内容，判断分类
2. 生成新的文档名（格式：{分类}-{主题}）
3. 复制到新分类文件夹
4. 原始文档保留在V2备份文件夹
"""

import os
import sys
import io
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# 修复Windows控制台编码
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# 分类判断规则（基于关键词和内容特征）
CATEGORY_RULES = {
    "历史文化": {
        "keywords": ["历史", "文化", "朝代", "古代", "人物", "传记", "皇帝", "将军", "战争",
                     "明朝", "清朝", "汉朝", "唐朝", "宋朝", "民国", "三国", "春秋",
                     "战国", "史记", "文献", "典故", "传统", "文明", "民俗", "风俗",
                     "诗词", "古文", "书法", "遗址", "文物", "古战场", "文化遗产"],
        "weight": 1.5
    },
    "营养健康": {
        "keywords": ["营养", "健康", "饮食", "食物", "蔬菜", "水果", "蛋白质",
                     "中医", "养生", "药膳", "食疗", "中药", "经络", "穴位", "调理",
                     "体质", "气血", "疾病", "预防", "治疗", "症状", "血压", "血糖",
                     "维生素", "膳食", "抗炎", "肠道", "益生菌", "减肥", "食谱"],
        "weight": 1.5
    },
    "生活方式": {
        "keywords": ["生活", "运动", "睡眠", "压力", "情绪", "心理", "作息", "习惯",
                     "美容", "护肤", "健身", "锻炼", "瑜伽", "整理", "收纳", "家居",
                     "理财", "工作", "效率"],
        "weight": 1.2
    },
    "教育育儿": {
        "keywords": ["育儿", "宝宝", "孩子", "教育", "辅食", "喂养", "早教",
                     "亲子", "成长", "发育", "妈妈", "孕妇", "新生儿",
                     "婴儿", "幼儿", "儿童", "学习", "学校"],
        "weight": 1.5
    },
    "旅游攻略": {
        "keywords": ["旅游", "旅行", "景点", "攻略", "出行", "交通", "酒店",
                     "民宿", "美食", "打卡", "签证", "机票", "行程", "路线",
                     "城市", "自驾", "自驾游", "环线", "赏枫"],
        "weight": 1.3
    },
    "摄影技巧": {
        "keywords": ["摄影", "拍照", "拍摄", "技巧", "曝光", "构图", "焦距",
                     "光圈", "快门", "ISO", "烟花", "街拍", "雨滴", "风景"],
        "weight": 2.0
    },
    "植物养护": {
        "keywords": ["植物", "养护", "种植", "盆栽", "花卉", "月季", "番茄",
                     "杀虫", "虫害", "高产", "盆景", "蜡梅", "花园"],
        "weight": 2.0
    },
    "综合知识": {
        "keywords": ["科普", "知识", "研究", "数据", "分布图", "地图",
                     "指南", "实用", "建议", "推荐"],
        "weight": 0.8
    }
}

def extract_content_summary(content: str, max_chars: int = 2000) -> str:
    """提取文档内容摘要"""
    # 去掉元信息
    content = re.sub(r'^>.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    content = re.sub(r'\*本文档由.*?生成\*', '', content)

    # 取前max_chars字符
    summary = content[:max_chars].strip()
    return summary

def extract_title(content: str) -> str:
    """提取文档标题"""
    lines = content.split('\n')
    for line in lines[:10]:
        line = line.strip()
        if line.startswith('# '):
            return line[2:].strip()
        if re.match(r'^[\u4e00-\u9fa5]{4,20}$', line):
            return line
    return ""

def classify_content(content: str) -> Tuple[str, float, str]:
    """
    分析内容，返回 (分类, 置信度, 分类理由)
    """
    summary = extract_content_summary(content)
    title = extract_title(content)

    # 合并标题和摘要进行判断
    full_text = f"{title} {summary}"

    scores = {}
    matched_keywords = {}

    for cat_name, rule in CATEGORY_RULES.items():
        score = 0
        found_kws = []

        for kw in rule["keywords"]:
            if kw in full_text:
                score += 1
                found_kws.append(kw)

        # 加权
        score *= rule["weight"]
        scores[cat_name] = score
        matched_keywords[cat_name] = found_kws

    if not scores or max(scores.values()) == 0:
        return "综合知识", 0.5, "无特定关键词匹配"

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    # 归一化置信度
    max_possible = 10 * 1.5  # 假设最多10个关键词匹配
    confidence = min(best_score / max_possible, 1.0)

    reason = f"匹配关键词: {', '.join(matched_keywords[best_cat][:5])}"

    return best_cat, confidence, reason

def generate_new_doc_name(original_name: str, category: str, content: str) -> str:
    """生成新的文档名（V7格式：{分类}-{主题}）"""
    # 去掉编号前缀
    name = re.sub(r'^\d{2}_', '', original_name)
    name = name.replace('.md', '')

    # 提取主题
    title = extract_title(content)
    if title and len(title) >= 2:
        # 清理标题
        topic = re.sub(r'[<>:"/\\|?*\n\r]', '', title).strip()
        topic = topic[:30]  # 限制长度
    else:
        topic = name

    return f"{category}-{topic}"

def main():
    base_dir = Path(r"d:\新建文件夹\处理结果")
    v2_archive = base_dir / "V2归档"
    v2_backup = base_dir / "V2备份"
    results_dir = base_dir

    # 确保备份文件夹存在
    v2_backup.mkdir(exist_ok=True)

    # 收集所有需要分类的文档
    md_files = list(v2_archive.glob("*.md"))
    docx_files = list(v2_archive.glob("*.docx"))

    print(f"=== V2文档AI重分类 ===")
    print(f"发现 {len(md_files)} 个Markdown文档")
    print(f"发现 {len(docx_files)} 个Word文档")
    print()

    results = []
    categories_count = {}

    # 处理每个Markdown文档
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')

            # AI分类
            category, confidence, reason = classify_content(content)

            # 生成新文档名
            new_doc_name = generate_new_doc_name(md_file.stem, category, content)

            # 创建分类目录
            cat_dir = results_dir / category
            cat_dir.mkdir(exist_ok=True)

            # 复制到新位置（带新名称）
            new_md_path = cat_dir / f"{new_doc_name}.md"

            # 处理重名
            counter = 1
            while new_md_path.exists():
                new_md_path = cat_dir / f"{new_doc_name}_{counter}.md"
                counter += 1

            shutil.copy2(md_file, new_md_path)

            # 同时复制到V2备份
            backup_path = v2_backup / md_file.name
            if not backup_path.exists():
                shutil.copy2(md_file, backup_path)

            # 复制对应的docx（如果有）
            docx_file = v2_archive / f"{md_file.stem}.docx"
            if docx_file.exists():
                new_docx_path = cat_dir / f"{new_md_path.stem}.docx"
                counter = 1
                while new_docx_path.exists():
                    new_docx_path = cat_dir / f"{new_md_path.stem}_{counter}.docx"
                    counter += 1
                shutil.copy2(docx_file, new_docx_path)

                backup_docx = v2_backup / docx_file.name
                if not backup_docx.exists():
                    shutil.copy2(docx_file, backup_docx)

            # 记录结果
            result = {
                "original": md_file.name,
                "category": category,
                "confidence": confidence,
                "reason": reason,
                "new_name": new_md_path.name
            }
            results.append(result)

            # 统计
            categories_count[category] = categories_count.get(category, 0) + 1

            # 输出
            print(f"[OK] {md_file.name}")
            print(f"  -> {category}/{new_doc_name}.md")
            print(f"  Confidence: {confidence:.2f} | {reason}")
            print()

        except Exception as e:
            print(f"[FAIL] {md_file.name}: {e}")
            print()

    # 输出统计
    print("\n" + "="*50)
    print("Classfication Statistics")
    print("="*50)
    for cat, count in sorted(categories_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count} docs")

    # 保存分类结果到JSON
    report_path = base_dir / "V2重分类结果.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_docs": len(results),
            "categories": categories_count,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Classification completed! Report saved to: {report_path}")
    print(f"[OK] Original docs copied to: {v2_backup}")

if __name__ == "__main__":
    main()
