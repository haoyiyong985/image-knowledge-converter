#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分类管理工具
============

命令行工具，用于分类管理和测试。

Usage:
    python classify.py classify "内容文本"
    python classify.py suggest "内容文本"
    python classify.py list
    python classify.py info <category_id>
    python classify.py explain "内容文本"
    python classify.py batch <file.txt>

Author: knowledge-converter
Version: 1.0.0
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.classifier_engine import ClassifierEngine


def cmd_classify(engine, args):
    """分类命令"""
    content = args.content
    threshold = args.threshold or 0.3
    multi = args.multi

    results = engine.classify(content, threshold=threshold, multi_class=multi)

    if not results:
        print("未找到匹配的分类")
        return 1

    print(f"\n内容: {content[:60]}{'...' if len(content) > 60 else ''}")
    print("-" * 50)

    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r.category_name}")
        print(f"    分类ID: {r.category_id}")
        print(f"    目标文档: {r.document}")
        print(f"    置信度: {r.confidence:.2%}")
        print(f"    匹配类型: {r.match_type}")
        if r.matched_keywords:
            print(f"    匹配关键词: {', '.join(r.matched_keywords)}")

    return 0


def cmd_suggest(engine, args):
    """建议命令"""
    content = args.content
    top_k = args.top_k or 3

    suggestions = engine.suggest(content, top_k=top_k)

    print(f"\n内容: {content[:60]}{'...' if len(content) > 60 else ''}")
    print("-" * 50)
    print(f"\n推荐分类 (Top {len(suggestions)}):")

    for i, cat_id in enumerate(suggestions, 1):
        cat_info = engine.get_category_info(cat_id)
        if cat_info:
            print(f"  [{i}] {cat_info['name']} ({cat_id})")
        else:
            print(f"  [{i}] {cat_id}")

    return 0


def cmd_explain(engine, args):
    """解释命令"""
    content = args.content

    explanation = engine.explain_classification(content)

    print(f"\n内容预览: {explanation['input_preview']}")
    print(f"内容长度: {explanation['input_length']} 字符")
    print("-" * 50)
    print(f"\n候选分类 ({len(explanation['categories'])}):")

    for i, cat in enumerate(explanation['categories'], 1):
        print(f"\n[{i}] {cat['name']} ({cat['id']})")
        print(f"    置信度: {cat['confidence']:.2%}")
        print(f"    匹配类型: {cat['match_type']}")
        print(f"    优先级: {cat['priority']}")
        print(f"    目标文档: {cat['document']}")
        if cat['matched_keywords']:
            print(f"    匹配关键词: {', '.join(cat['matched_keywords'])}")

    return 0


def cmd_list(engine, args):
    """列出所有分类"""
    categories = engine.get_categories()

    print(f"\n可用分类 ({len(categories)}):")
    print("-" * 50)

    for cat in categories:
        keywords_count = len(cat.get('keywords', []))
        print(f"\n[{cat['id']}] {cat['name']}")
        print(f"    文档: {cat.get('document', 'N/A')}")
        print(f"    关键词: {keywords_count} 个")
        print(f"    优先级: {cat.get('priority', 0)}")
        if cat.get('description'):
            print(f"    描述: {cat['description']}")

    return 0


def cmd_info(engine, args):
    """显示分类详情"""
    cat_info = engine.get_category_info(args.category_id)

    if not cat_info:
        print(f"未找到分类: {args.category_id}")
        return 1

    print(f"\n分类详情: {cat_info['name']}")
    print("-" * 50)
    print(f"ID: {cat_info['id']}")
    print(f"名称: {cat_info['name']}")
    print(f"文档: {cat_info.get('document', 'N/A')}")
    print(f"优先级: {cat_info.get('priority', 0)}")
    print(f"启用: {cat_info.get('enabled', True)}")

    if cat_info.get('description'):
        print(f"\n描述:\n  {cat_info['description']}")

    keywords = cat_info.get('keywords', [])
    if keywords:
        print(f"\n关键词 ({len(keywords)}):")
        for i in range(0, len(keywords), 5):
            print(f"  {', '.join(keywords[i:i+5])}")

    return 0


def cmd_batch(engine, args):
    """批量分类"""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"文件不存在: {file_path}")
        return 1

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    results = []
    for i, line in enumerate(lines, 1):
        content = line.strip()
        if not content:
            continue

        suggestions = engine.suggest(content, top_k=1)
        result = {
            'line': i,
            'content': content[:50] + '...' if len(content) > 50 else content,
            'category': suggestions[0] if suggestions else 'unknown'
        }
        results.append(result)
        print(f"[{i:3d}] {result['category']:15s} | {result['content']}")

    print(f"\n总计: {len(results)} 条记录")

    # 保存结果
    output_file = file_path.with_suffix('.classified.txt')
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(f"{r['category']}\t{r['content']}\n")
    print(f"结果已保存到: {output_file}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='分类管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python classify.py classify "抗炎饮食金字塔"
  python classify.py suggest "宝宝辅食添加" --top-k 5
  python classify.py explain "这是一篇关于中医养生的文章"
  python classify.py list
  python classify.py info nutrition
  python classify.py batch content.txt
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='子命令')

    # classify 命令
    classify_parser = subparsers.add_parser('classify', help='对内容进行分类')
    classify_parser.add_argument('content', help='待分类的内容')
    classify_parser.add_argument('--threshold', '-t', type=float, help='置信度阈值 (默认: 0.3)')
    classify_parser.add_argument('--multi', '-m', action='store_true', help='返回多个分类')

    # suggest 命令
    suggest_parser = subparsers.add_parser('suggest', help='获取分类建议')
    suggest_parser.add_argument('content', help='待分类的内容')
    suggest_parser.add_argument('--top-k', '-k', type=int, help='返回前K个建议 (默认: 3)')

    # explain 命令
    explain_parser = subparsers.add_parser('explain', help='获取分类详细解释')
    explain_parser.add_argument('content', help='待分类的内容')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有分类')

    # info 命令
    info_parser = subparsers.add_parser('info', help='显示分类详情')
    info_parser.add_argument('category_id', help='分类ID')

    # batch 命令
    batch_parser = subparsers.add_parser('batch', help='批量分类文件')
    batch_parser.add_argument('file', help='包含待分类内容的文件')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # 初始化分类器
    engine = ClassifierEngine()

    # 执行命令
    commands = {
        'classify': cmd_classify,
        'suggest': cmd_suggest,
        'explain': cmd_explain,
        'list': cmd_list,
        'info': cmd_info,
        'batch': cmd_batch,
    }

    return commands[args.command](engine, args)


if __name__ == '__main__':
    sys.exit(main())
