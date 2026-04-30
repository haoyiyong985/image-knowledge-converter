#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库管理模块 - 负责内容分类、索引管理和搜索功能
"""

import os
import json
import yaml
import hashlib
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import re
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeEntry:
    """知识条目数据类"""
    id: str
    title: str
    content: str
    category: str
    keywords: List[str]
    summary: str
    source_file: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict
    tables: List[Dict]


@dataclass
class SearchResult:
    """搜索结果数据类"""
    entry: KnowledgeEntry
    relevance_score: float
    matched_keywords: List[str]


class CategoryManager:
    """分类管理器"""
    
    def __init__(self, config_path: str = "config/categories.yaml"):
        self.config_path = config_path
        self.categories = self._load_categories()
        
    def _load_categories(self) -> Dict:
        """加载分类配置"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return {cat['id']: cat for cat in config.get('categories', [])}
        return {}
    
    def get_category(self, category_id: str) -> Optional[Dict]:
        """获取分类信息"""
        return self.categories.get(category_id)
    
    def get_all_categories(self) -> List[Dict]:
        """获取所有分类"""
        return list(self.categories.values())
    
    def get_category_keywords(self, category_id: str) -> List[str]:
        """获取分类关键词"""
        category = self.categories.get(category_id)
        return category.get('keywords', []) if category else []


class MetadataExtractor:
    """元数据提取器"""
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> set:
        """加载停用词"""
        # 常见中文停用词
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', 
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '之', '与', '及', '等', '或', '但', '而', '如果', '因为',
            '所以', '虽然', '但是', '可以', '需要', '进行', '通过', '使用'
        }
    
    def extract_title(self, text: str, max_length: int = 100) -> str:
        """
        提取标题
        
        Args:
            text: 文本内容
            max_length: 最大长度
            
        Returns:
            标题
        """
        lines = text.strip().split('\n')
        
        # 尝试从第一行提取
        for line in lines[:3]:
            line = line.strip()
            if len(line) > 5 and len(line) <= max_length:
                # 清理标题
                title = re.sub(r'[#\*\-\=]+', '', line).strip()
                if title:
                    return title
        
        # 如果没有合适的标题，返回前50个字符
        return text[:min(50, len(text))].strip() + "..."
    
    def extract_keywords(self, text: str, max_count: int = 10) -> List[str]:
        """
        提取关键词
        
        Args:
            text: 文本内容
            max_count: 最大关键词数量
            
        Returns:
            关键词列表
        """
        # 简单的词频统计
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', text.lower())
        
        # 过滤停用词和短词
        filtered_words = [w for w in words if w not in self.stopwords and len(w) >= 2]
        
        # 统计词频
        word_freq = defaultdict(int)
        for word in filtered_words:
            word_freq[word] += 1
        
        # 返回频率最高的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_count]]
    
    def generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        生成摘要
        
        Args:
            text: 文本内容
            max_length: 最大长度
            
        Returns:
            摘要
        """
        # 简单的摘要生成：取前几句话
        sentences = re.split(r'[。！？.!?]', text)
        
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                if len(summary) + len(sentence) <= max_length:
                    summary += sentence + "。"
                else:
                    break
        
        if not summary:
            summary = text[:max_length] + "..."
        
        return summary


class KnowledgeBase:
    """知识库主类"""
    
    def __init__(self, base_path: str = "knowledge_base"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.category_manager = CategoryManager()
        self.metadata_extractor = MetadataExtractor()
        
        # 创建分类目录
        for category in self.category_manager.get_all_categories():
            cat_path = self.base_path / category['id']
            cat_path.mkdir(exist_ok=True)
        
        # 索引目录
        self.index_path = self.base_path / "index"
        self.index_path.mkdir(exist_ok=True)
        
        # 加载索引
        self.index = self._load_index()
    
    def _load_index(self) -> Dict:
        """加载索引"""
        index_file = self.index_path / "knowledge_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'entries': {},
            'categories': defaultdict(list),
            'keywords': defaultdict(list),
            'timeline': []
        }
    
    def _save_index(self):
        """保存索引"""
        index_file = self.index_path / "knowledge_index.json"
        
        # 转换defaultdict为普通dict
        index_to_save = {
            'entries': self.index['entries'],
            'categories': dict(self.index['categories']),
            'keywords': dict(self.index['keywords']),
            'timeline': self.index['timeline']
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_to_save, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self, content: str) -> str:
        """生成唯一ID"""
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def add_entry(self, content: str, source_file: str, category: str = None, 
                  tables: List[Dict] = None) -> KnowledgeEntry:
        """
        添加知识条目
        
        Args:
            content: 文本内容
            source_file: 源文件路径
            category: 分类（可选）
            tables: 表格数据
            
        Returns:
            知识条目
        """
        # 生成ID
        entry_id = self._generate_id(content)
        
        # 检查是否已存在
        if entry_id in self.index['entries']:
            logger.info(f"条目已存在: {entry_id}")
            existing = self.index['entries'][entry_id]
            return KnowledgeEntry(**existing)
        
        # 提取元数据
        title = self.metadata_extractor.extract_title(content)
        keywords = self.metadata_extractor.extract_keywords(content)
        summary = self.metadata_extractor.generate_summary(content)
        
        # 确定分类
        if not category:
            category = self._auto_classify(content, keywords)
        
        # 创建条目
        now = datetime.now()
        entry = KnowledgeEntry(
            id=entry_id,
            title=title,
            content=content,
            category=category,
            keywords=keywords,
            summary=summary,
            source_file=source_file,
            created_at=now,
            updated_at=now,
            metadata={
                'word_count': len(content),
                'char_count': len(content.replace(' ', '').replace('\n', ''))
            },
            tables=tables or []
        )
        
        # 保存条目
        self._save_entry_file(entry)
        
        # 更新索引
        self._update_index(entry)
        
        logger.info(f"添加条目: {title} (分类: {category})")
        
        return entry
    
    def _save_entry_file(self, entry: KnowledgeEntry):
        """保存条目到文件"""
        category_path = self.base_path / entry.category
        category_path.mkdir(exist_ok=True)
        
        entry_file = category_path / f"{entry.id}.json"
        
        # 转换为可序列化的字典
        entry_dict = {
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'category': entry.category,
            'keywords': entry.keywords,
            'summary': entry.summary,
            'source_file': entry.source_file,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat(),
            'metadata': entry.metadata,
            'tables': entry.tables
        }
        
        with open(entry_file, 'w', encoding='utf-8') as f:
            json.dump(entry_dict, f, ensure_ascii=False, indent=2)
    
    def _update_index(self, entry: KnowledgeEntry):
        """更新索引"""
        # 添加条目到索引
        self.index['entries'][entry.id] = {
            'id': entry.id,
            'title': entry.title,
            'category': entry.category,
            'keywords': entry.keywords,
            'summary': entry.summary,
            'source_file': entry.source_file,
            'created_at': entry.created_at.isoformat(),
            'updated_at': entry.updated_at.isoformat()
        }
        
        # 更新分类索引
        if entry.id not in self.index['categories'][entry.category]:
            self.index['categories'][entry.category].append(entry.id)
        
        # 更新关键词索引
        for keyword in entry.keywords:
            if entry.id not in self.index['keywords'][keyword]:
                self.index['keywords'][keyword].append(entry.id)
        
        # 更新时间线
        self.index['timeline'].append({
            'id': entry.id,
            'title': entry.title,
            'category': entry.category,
            'created_at': entry.created_at.isoformat()
        })
        
        # 保存索引
        self._save_index()
    
    def _auto_classify(self, content: str, keywords: List[str]) -> str:
        """
        自动分类
        
        Args:
            content: 文本内容
            keywords: 关键词
            
        Returns:
            分类ID
        """
        text = content.lower()
        category_scores = {}
        
        for cat_id, category in self.category_manager.categories.items():
            score = 0
            cat_keywords = category.get('keywords', [])
            
            for keyword in cat_keywords:
                if keyword.lower() in text:
                    score += 1
            
            # 关键词匹配
            for keyword in keywords:
                if keyword in cat_keywords:
                    score += 2
            
            if score > 0:
                category_scores[cat_id] = score
        
        if category_scores:
            # 返回得分最高的分类
            best_category = max(category_scores.items(), key=lambda x: x[1])
            return best_category[0]
        
        # 默认分类
        return 'life'
    
    def search(self, query: str, category: str = None, limit: int = 20) -> List[SearchResult]:
        """
        搜索知识条目
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            limit: 返回结果数量限制
            
        Returns:
            搜索结果列表
        """
        query_lower = query.lower()
        results = []
        
        for entry_id, entry_info in self.index['entries'].items():
            # 分类过滤
            if category and entry_info['category'] != category:
                continue
            
            score = 0
            matched_keywords = []
            
            # 标题匹配
            if query_lower in entry_info['title'].lower():
                score += 10
                matched_keywords.append('title')
            
            # 关键词匹配
            for keyword in entry_info['keywords']:
                if query_lower in keyword.lower():
                    score += 5
                    matched_keywords.append(keyword)
            
            # 摘要匹配
            if query_lower in entry_info['summary'].lower():
                score += 3
                matched_keywords.append('summary')
            
            if score > 0:
                # 加载完整条目
                entry = self._load_entry(entry_info['category'], entry_id)
                if entry:
                    results.append(SearchResult(
                        entry=entry,
                        relevance_score=score,
                        matched_keywords=list(set(matched_keywords))
                    ))
        
        # 按相关度排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return results[:limit]
    
    def _load_entry(self, category: str, entry_id: str) -> Optional[KnowledgeEntry]:
        """加载条目"""
        entry_file = self.base_path / category / f"{entry_id}.json"
        
        if not entry_file.exists():
            return None
        
        with open(entry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return KnowledgeEntry(
            id=data['id'],
            title=data['title'],
            content=data['content'],
            category=data['category'],
            keywords=data['keywords'],
            summary=data['summary'],
            source_file=data['source_file'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            metadata=data.get('metadata', {}),
            tables=data.get('tables', [])
        )
    
    def get_entries_by_category(self, category: str) -> List[KnowledgeEntry]:
        """
        获取分类下的所有条目
        
        Args:
            category: 分类ID
            
        Returns:
            条目列表
        """
        entries = []
        entry_ids = self.index['categories'].get(category, [])
        
        for entry_id in entry_ids:
            entry = self._load_entry(category, entry_id)
            if entry:
                entries.append(entry)
        
        return entries
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            'total_entries': len(self.index['entries']),
            'categories': {},
            'total_keywords': len(self.index['keywords']),
            'timeline_count': len(self.index['timeline'])
        }
        
        for category_id, entry_ids in self.index['categories'].items():
            category_info = self.category_manager.get_category(category_id)
            stats['categories'][category_id] = {
                'name': category_info['name'] if category_info else category_id,
                'count': len(entry_ids),
                'icon': category_info.get('icon', '📄') if category_info else '📄'
            }
        
        return stats
    
    def export_to_html(self, output_path: str):
        """
        导出为HTML
        
        Args:
            output_path: 输出文件路径
        """
        html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>知识库</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .stats { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card { 
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card h3 { color: #667eea; margin-bottom: 10px; }
        .category-section { 
            background: white;
            margin-bottom: 20px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .category-header { 
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
        }
        .category-header h2 { display: flex; align-items: center; gap: 10px; }
        .entry-list { padding: 20px; }
        .entry-item { 
            padding: 15px;
            border-bottom: 1px solid #e9ecef;
        }
        .entry-item:last-child { border-bottom: none; }
        .entry-title { 
            font-size: 1.2em;
            color: #667eea;
            margin-bottom: 5px;
        }
        .entry-summary { color: #666; font-size: 0.9em; }
        .entry-meta { 
            color: #999;
            font-size: 0.8em;
            margin-top: 5px;
        }
        .keywords { 
            display: flex;
            gap: 5px;
            margin-top: 10px;
            flex-wrap: wrap;
        }
        .keyword { 
            background: #e9ecef;
            padding: 3px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📚 我的知识库</h1>
            <p>自动整理的个人知识管理系统</p>
        </header>
"""
        
        # 添加统计
        stats = self.get_statistics()
        html_content += '<div class="stats">'
        html_content += f'''
            <div class="stat-card">
                <h3>📄 总条目数</h3>
                <p style="font-size: 2em; color: #667eea;">{stats['total_entries']}</p>
            </div>
            <div class="stat-card">
                <h3>🏷️ 关键词数</h3>
                <p style="font-size: 2em; color: #667eea;">{stats['total_keywords']}</p>
            </div>
            <div class="stat-card">
                <h3>📁 分类数</h3>
                <p style="font-size: 2em; color: #667eea;">{len(stats['categories'])}</p>
            </div>
        </div>
        '''
        
        # 添加分类内容
        for category_id, category_stat in stats['categories'].items():
            entries = self.get_entries_by_category(category_id)
            
            html_content += f'''
            <div class="category-section">
                <div class="category-header">
                    <h2>{category_stat['icon']} {category_stat['name']} <span style="color: #999; font-size: 0.7em;">({category_stat['count']})</span></h2>
                </div>
                <div class="entry-list">
            '''
            
            for entry in entries:
                keywords_html = ''.join([f'<span class="keyword">{k}</span>' for k in entry.keywords[:5]])
                html_content += f'''
                    <div class="entry-item">
                        <div class="entry-title">{entry.title}</div>
                        <div class="entry-summary">{entry.summary[:150]}...</div>
                        <div class="entry-meta">来源: {entry.source_file} | 创建: {entry.created_at.strftime('%Y-%m-%d')}</div>
                        <div class="keywords">{keywords_html}</div>
                    </div>
                '''
            
            html_content += '</div></div>'
        
        html_content += '''
    </div>
</body>
</html>
        '''
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"知识库已导出到: {output_path}")


if __name__ == '__main__':
    # 测试代码
    kb = KnowledgeBase()
    
    # 添加测试条目
    test_content = """
    Python编程入门指南
    
    Python是一种高级编程语言，以其简洁的语法和强大的功能而闻名。
    
    主要特点：
    1. 简单易学
    2. 丰富的库
    3. 跨平台
    4. 广泛应用
    
    适合初学者学习编程的首选语言。
    """
    
    entry = kb.add_entry(test_content, "test.txt")
    print(f"添加条目: {entry.title}")
    print(f"分类: {entry.category}")
    print(f"关键词: {entry.keywords}")
    
    # 搜索测试
    results = kb.search("Python")
    print(f"\n搜索结果: 找到 {len(results)} 条")
    
    # 导出测试
    kb.export_to_html("knowledge_base/index.html")
