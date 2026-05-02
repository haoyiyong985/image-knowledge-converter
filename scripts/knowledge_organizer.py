#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识整理系统控制器 - 主程序入口，协调所有模块工作
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from image_processor import ImageProcessor, ProcessedImage
from knowledge_manager import KnowledgeBase, KnowledgeEntry
from classifier_engine import ClassifierEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/knowledge_organizer.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class KnowledgeOrganizer:
    """知识整理系统主类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化知识整理系统
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        
        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)
        
        # 初始化各个模块
        logger.info("正在初始化知识整理系统...")
        
        try:
            self.image_processor = ImageProcessor(config_path)
            self.knowledge_base = KnowledgeBase()
            self.classifier = ClassifierEngine()
            
            logger.info("系统初始化完成")
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            raise
    
    def process_images(self, input_dir: str = "images/raw", 
                      output_dir: str = "output") -> List[ProcessedImage]:
        """
        处理图片目录中的所有图片
        
        Args:
            input_dir: 输入图片目录
            output_dir: 输出目录
            
        Returns:
            处理后的图片列表
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return []
        
        # 获取所有图片文件
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
        image_files = [
            f for f in input_path.iterdir() 
            if f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            logger.warning(f"在 {input_dir} 中未找到图片文件")
            return []
        
        logger.info(f"找到 {len(image_files)} 张图片，开始处理...")
        
        results = []
        for i, image_file in enumerate(image_files, 1):
            logger.info(f"处理第 {i}/{len(image_files)} 张图片: {image_file.name}")
            
            try:
                result = self.image_processor.process_image(
                    str(image_file), 
                    output_dir=output_dir
                )
                results.append(result)
                
                # 保存处理结果
                self.image_processor.save_results(
                    result, 
                    output_dir, 
                    formats=['txt', 'json']
                )
                
            except Exception as e:
                logger.error(f"处理图片失败 {image_file}: {e}")
        
        logger.info(f"图片处理完成: 成功 {len(results)}/{len(image_files)}")
        return results
    
    def import_to_knowledge_base(self, processed_images: List[ProcessedImage],
                                  auto_classify: bool = True) -> List[KnowledgeEntry]:
        """
        将处理后的图片导入知识库
        
        Args:
            processed_images: 处理后的图片列表
            auto_classify: 是否自动分类
            
        Returns:
            导入的知识条目列表
        """
        entries = []
        
        for processed in processed_images:
            if not processed.ocr_result or not processed.ocr_result.text:
                logger.warning(f"跳过无文本内容的图片: {processed.original_path}")
                continue
            
            try:
                # 自动分类
                category = None
                if auto_classify:
                    classification = self.classifier.classify(processed.ocr_result.text)
                    category = classification.category
                    logger.info(f"自动分类结果: {category} (置信度: {classification.confidence:.2f})")
                
                # 准备表格数据
                tables = []
                for table in processed.tables:
                    tables.append({
                        'headers': table.headers,
                        'rows': table.rows,
                        'confidence': table.confidence
                    })
                
                # 添加到知识库
                entry = self.knowledge_base.add_entry(
                    content=processed.ocr_result.text,
                    source_file=processed.original_path,
                    category=category,
                    tables=tables
                )
                
                entries.append(entry)
                
                # 添加到相似度索引
                self.classifier.add_to_similarity_index(
                    entry.id, 
                    processed.ocr_result.text
                )
                
                logger.info(f"已导入知识库: {entry.title} (分类: {entry.category})")
                
            except Exception as e:
                logger.error(f"导入知识库失败: {processed.original_path}, 错误: {e}")
        
        logger.info(f"知识库导入完成: 共 {len(entries)} 条")
        return entries
    
    def search(self, query: str, category: str = None, limit: int = 20) -> List:
        """
        搜索知识库
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            limit: 结果数量限制
            
        Returns:
            搜索结果列表
        """
        logger.info(f"搜索: '{query}' (分类: {category})")
        
        results = self.knowledge_base.search(query, category, limit)
        
        logger.info(f"找到 {len(results)} 条结果")
        return results
    
    def get_statistics(self) -> dict:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        return self.knowledge_base.get_statistics()
    
    def export(self, format: str = "html", output_path: str = None):
        """
        导出知识库
        
        Args:
            format: 导出格式 (html, json)
            output_path: 输出路径
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/knowledge_base_{timestamp}.{format}"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if format == "html":
            self.knowledge_base.export_to_html(output_path)
        elif format == "json":
            # 导出为JSON
            stats = self.get_statistics()
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            logger.info(f"统计信息已导出到: {output_path}")
        else:
            logger.error(f"不支持的导出格式: {format}")
    
    def interactive_mode(self):
        """交互式模式"""
        print("\n" + "="*50)
        print("🎉 欢迎使用图片转知识库系统")
        print("="*50 + "\n")
        
        while True:
            print("\n可用命令:")
            print("  1. process  - 处理图片")
            print("  2. import   - 导入到知识库")
            print("  3. search   - 搜索知识库")
            print("  4. stats    - 查看统计")
            print("  5. export   - 导出知识库")
            print("  6. quit     - 退出")
            
            command = input("\n请输入命令: ").strip().lower()
            
            if command in ['1', 'process']:
                input_dir = input("请输入图片目录 (默认: images/raw): ").strip() or "images/raw"
                self.process_images(input_dir)
                
            elif command in ['2', 'import']:
                # 重新处理并导入
                results = self.process_images()
                if results:
                    self.import_to_knowledge_base(results)
                
            elif command in ['3', 'search']:
                query = input("请输入搜索关键词: ").strip()
                if query:
                    results = self.search(query)
                    print(f"\n找到 {len(results)} 条结果:")
                    for i, result in enumerate(results[:10], 1):
                        print(f"\n{i}. {result.entry.title}")
                        print(f"   分类: {result.entry.category}")
                        print(f"   相关度: {result.relevance_score:.2f}")
                        print(f"   {result.entry.summary[:100]}...")
                
            elif command in ['4', 'stats']:
                stats = self.get_statistics()
                print("\n📊 知识库统计:")
                print(f"  总条目数: {stats['total_entries']}")
                print(f"  关键词数: {stats['total_keywords']}")
                print(f"  分类统计:")
                for cat_id, cat_info in stats['categories'].items():
                    print(f"    {cat_info['icon']} {cat_info['name']}: {cat_info['count']} 条")
                
            elif command in ['5', 'export']:
                format_type = input("请输入导出格式 (html/json, 默认: html): ").strip() or "html"
                self.export(format=format_type)
                
            elif command in ['6', 'quit', 'exit', 'q']:
                print("感谢使用，再见！")
                break
                
            else:
                print("未知命令，请重新输入")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='图片转知识库系统 - 将图片内容转换为结构化知识库',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 处理图片
  python knowledge_organizer.py process --input images/raw --output output
  
  # 导入到知识库
  python knowledge_organizer.py import
  
  # 搜索知识库
  python knowledge_organizer.py search "Python"
  
  # 查看统计
  python knowledge_organizer.py stats
  
  # 导出知识库
  python knowledge_organizer.py export --format html
  
  # 交互式模式
  python knowledge_organizer.py --interactive
        """
    )
    
    parser.add_argument('command', nargs='?', 
                       choices=['process', 'import', 'search', 'stats', 'export'],
                       help='要执行的命令')
    parser.add_argument('--input', '-i', default='images/raw',
                       help='输入图片目录 (默认: images/raw)')
    parser.add_argument('--output', '-o', default='output',
                       help='输出目录 (默认: output)')
    parser.add_argument('--category', '-c',
                       help='分类过滤')
    parser.add_argument('--format', '-f', default='html',
                       choices=['html', 'json'],
                       help='导出格式 (默认: html)')
    parser.add_argument('--interactive', '-I', action='store_true',
                       help='进入交互式模式')
    parser.add_argument('--query', '-q',
                       help='搜索关键词')
    
    args = parser.parse_args()
    
    # 创建系统实例
    organizer = KnowledgeOrganizer()
    
    # 交互式模式
    if args.interactive:
        organizer.interactive_mode()
        return
    
    # 命令模式
    if args.command == 'process':
        organizer.process_images(args.input, args.output)
        
    elif args.command == 'import':
        results = organizer.process_images(args.input, args.output)
        if results:
            organizer.import_to_knowledge_base(results)
            
    elif args.command == 'search':
        query = args.query or input("请输入搜索关键词: ")
        if query:
            results = organizer.search(query, args.category)
            print(f"\n找到 {len(results)} 条结果:")
            for i, result in enumerate(results[:10], 1):
                print(f"\n{i}. {result.entry.title}")
                print(f"   分类: {result.entry.category}")
                print(f"   相关度: {result.relevance_score:.2f}")
                print(f"   {result.entry.summary[:100]}...")
                
    elif args.command == 'stats':
        stats = organizer.get_statistics()
        print("\n📊 知识库统计:")
        print(f"  总条目数: {stats['total_entries']}")
        print(f"  关键词数: {stats['total_keywords']}")
        print(f"  分类统计:")
        for cat_id, cat_info in stats['categories'].items():
            print(f"    {cat_info['icon']} {cat_info['name']}: {cat_info['count']} 条")
            
    elif args.command == 'export':
        organizer.export(format=args.format)
        
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
