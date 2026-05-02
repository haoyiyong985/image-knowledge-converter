#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示脚本 - 展示图片转知识库系统的完整工作流程
"""

import os
import sys
from pathlib import Path

# 确保可以导入本地模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from knowledge_organizer import KnowledgeOrganizer
from knowledge_manager import KnowledgeBase
from classifier_engine import ClassifierEngine


def print_section(title):
    """打印章节标题"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def demo_classification():
    """演示分类功能"""
    print_section("演示 1: 智能分类")
    
    classifier = ClassifierEngine()
    
    test_texts = [
        ("Python是一种强大的编程语言，适合数据分析和人工智能开发。", "技术文档"),
        ("今天学习了高等数学中的微积分，感觉很有趣。", "学习笔记"),
        ("公司年会总结报告，今年的业绩增长了20%。", "工作资料"),
        ("周末去爬山，风景很美，空气很清新。", "生活记录"),
        ("股票投资策略分享，如何选择优质股票。", "财务理财"),
        ("健康饮食指南，多吃蔬菜水果有益身体。", "健康养生"),
    ]
    
    print("\n测试文本分类:\n")
    for text, expected in test_texts:
        result = classifier.classify(text, use_ml=False)
        status = "✓" if result.category in ["technology", "study", "work", "life", "finance", "health"] else "✗"
        print(f"{status} 文本: {text[:30]}...")
        print(f"   预期: {expected}")
        print(f"   分类: {result.category} (置信度: {result.confidence:.2f})")
        print()


def demo_knowledge_base():
    """演示知识库功能"""
    print_section("演示 2: 知识库管理")
    
    kb = KnowledgeBase()
    
    # 添加示例条目
    sample_entries = [
        {
            "content": """
            Python编程最佳实践
            
            1. 代码风格遵循PEP 8
            2. 使用虚拟环境管理依赖
            3. 编写单元测试保证代码质量
            4. 使用类型提示提高代码可读性
            5. 合理使用列表推导式和生成器
            
            Python的优雅之处在于简洁而强大的语法。
            """,
            "category": "technology",
            "source": "sample_python.txt"
        },
        {
            "content": """
            高等数学学习笔记 - 微积分基础
            
            导数的定义：
            f'(x) = lim(h→0) [f(x+h) - f(x)] / h
            
            基本求导法则：
            - 常数法则：(c)' = 0
            - 幂函数法则：(x^n)' = nx^(n-1)
            - 和差法则：(u±v)' = u' ± v'
            - 乘积法则：(uv)' = u'v + uv'
            
            微积分是数学分析的基础。
            """,
            "category": "study",
            "source": "sample_math.txt"
        },
        {
            "content": """
            2024年第一季度工作总结
            
            主要成果：
            1. 完成产品迭代3个版本
            2. 用户增长率达到25%
            3. 优化系统性能，响应时间减少40%
            4. 团队扩充至15人
            
            下季度计划：
            - 推出新功能模块
            - 提升用户满意度
            - 加强团队培训
            """,
            "category": "work",
            "source": "sample_work.txt"
        }
    ]
    
    print("\n添加示例条目到知识库:\n")
    for entry_data in sample_entries:
        entry = kb.add_entry(
            content=entry_data["content"],
            source_file=entry_data["source"],
            category=entry_data["category"]
        )
        print(f"✓ 已添加: {entry.title}")
        print(f"   分类: {entry.category}")
        print(f"   关键词: {', '.join(entry.keywords[:5])}")
        print()
    
    # 搜索演示
    print("\n搜索演示:\n")
    search_queries = ["Python", "数学", "工作"]
    
    for query in search_queries:
        results = kb.search(query)
        print(f"搜索 '{query}': 找到 {len(results)} 条结果")
        for result in results[:3]:
            print(f"  - {result.entry.title} (相关度: {result.relevance_score:.2f})")
        print()
    
    # 统计信息
    print("\n知识库统计:\n")
    stats = kb.get_statistics()
    print(f"总条目数: {stats['total_entries']}")
    print(f"关键词数: {stats['total_keywords']}")
    print("分类分布:")
    for cat_id, cat_info in stats['categories'].items():
        print(f"  {cat_info['icon']} {cat_info['name']}: {cat_info['count']} 条")


def demo_full_workflow():
    """演示完整工作流程"""
    print_section("演示 3: 完整工作流程")
    
    print("""
本演示展示了图片转知识库系统的完整工作流程：

步骤 1: 图片预处理
  - 读取图片文件
  - 灰度转换
  - 对比度增强
  - 去噪处理
  - 二值化

步骤 2: OCR文字识别
  - 使用Tesseract引擎
  - 支持中英文混合
  - 提取文本和位置信息
  - 计算置信度

步骤 3: 表格检测
  - 检测表格区域
  - 识别行列结构
  - 提取单元格内容
  - 导出为CSV格式

步骤 4: 智能分类
  - 关键词匹配
  - 内容分析
  - 自动分类到6个类别
    * 技术文档 (technology)
    * 学习笔记 (study)
    * 工作资料 (work)
    * 生活记录 (life)
    * 财务理财 (finance)
    * 健康养生 (health)

步骤 5: 知识库存储
  - 提取元数据（标题、关键词、摘要）
  - 结构化存储
  - 建立索引
  - 更新分类统计

步骤 6: 搜索和导出
  - 关键词搜索
  - 分类浏览
  - 导出为HTML/JSON
  - 生成知识库报告
""")
    
    print("✓ 工作流程演示完成")


def demo_cli():
    """演示命令行接口"""
    print_section("演示 4: 命令行接口")
    
    print("""
系统提供以下命令行接口:

1. 处理图片
   python knowledge_organizer.py process --input images/raw --output output

2. 导入知识库
   python knowledge_organizer.py import

3. 搜索内容
   python knowledge_organizer.py search "关键词"

4. 查看统计
   python knowledge_organizer.py stats

5. 导出知识库
   python knowledge_organizer.py export --format html

6. 交互式模式
   python knowledge_organizer.py --interactive
""")


def main():
    """主函数"""
    print("\n" + "🎉"*20)
    print("\n   欢迎使用图片转知识库系统演示\n")
    print("🎉"*20 + "\n")
    
    print("""
本演示将展示系统的核心功能：
  1. 智能分类 - 自动识别内容类别
  2. 知识库管理 - 存储、搜索、统计
  3. 完整工作流程 - 从图片到知识库
  4. 命令行接口 - 各种操作命令
""")
    
    input("\n按回车键开始演示...")
    
    try:
        # 运行各个演示
        demo_classification()
        input("\n按回车键继续...")
        
        demo_knowledge_base()
        input("\n按回车键继续...")
        
        demo_full_workflow()
        input("\n按回车键继续...")
        
        demo_cli()
        
        print_section("演示完成")
        print("""
✅ 所有演示已完成！

系统已准备就绪，您可以：
  1. 将图片放入 images/raw/ 目录
  2. 运行: python knowledge_organizer.py process
  3. 运行: python knowledge_organizer.py import
  4. 查看知识库: knowledge_base/index.html

更多信息请查看:
  - README.md - 项目说明
  - USAGE_GUIDE.md - 使用指南
  - config/ - 配置文件

感谢使用图片转知识库系统！
""")
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
