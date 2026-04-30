#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类引擎 - 负责机器学习分类、关键词匹配和相似度计算
"""

import os
import re
import json
import pickle
import logging
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    category: str
    confidence: float
    probabilities: Dict[str, float]
    method: str


@dataclass
class SimilarityResult:
    """相似度结果数据类"""
    entry_id: str
    similarity_score: float
    content_preview: str


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        self.stopwords = self._load_stopwords()
    
    def _load_stopwords(self) -> set:
        """加载停用词"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去',
            '你', '会', '着', '没有', '看', '好', '自己', '这', '那',
            '之', '与', '及', '等', '或', '但', '而', '如果', '因为',
            '所以', '虽然', '但是', '可以', '需要', '进行', '通过', '使用',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'shall', 'can',
            'need', 'dare', 'ought', 'used', 'to', 'of', 'in', 'for',
            'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
            'during', 'before', 'after', 'above', 'below', 'between',
            'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'when', 'where', 'why', 'how', 'all', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'and',
            'but', 'if', 'or', 'because', 'until', 'while', 'this', 'that'
        }
    
    def preprocess(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 转换为小写
        text = text.lower()
        
        # 移除非字母数字字符（保留中文）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', text)
        
        # 分词（简单实现）
        words = re.findall(r'[\u4e00-\u9fff]{2,}|[a-zA-Z]+', text)
        
        # 过滤停用词和短词
        words = [w for w in words if w not in self.stopwords and len(w) >= 2]
        
        return ' '.join(words)


class KeywordClassifier:
    """关键词分类器"""
    
    def __init__(self, categories_config_path: str = "config/categories.yaml"):
        self.categories = self._load_categories(categories_config_path)
        self.text_preprocessor = TextPreprocessor()
    
    def _load_categories(self, config_path: str) -> Dict:
        """加载分类配置"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return {cat['id']: cat for cat in config.get('categories', [])}
        return {}
    
    def classify(self, text: str) -> ClassificationResult:
        """
        基于关键词进行分类
        
        Args:
            text: 文本内容
            
        Returns:
            分类结果
        """
        processed_text = self.text_preprocessor.preprocess(text)
        
        category_scores = {}
        
        for cat_id, category in self.categories.items():
            score = 0
            keywords = category.get('keywords', [])
            
            for keyword in keywords:
                keyword_lower = keyword.lower()
                # 计算关键词出现次数
                count = processed_text.count(keyword_lower)
                score += count
            
            if score > 0:
                category_scores[cat_id] = score
        
        if not category_scores:
            return ClassificationResult(
                category='life',
                confidence=0.0,
                probabilities={'life': 1.0},
                method='keyword_fallback'
            )
        
        # 计算概率
        total_score = sum(category_scores.values())
        probabilities = {
            cat: score / total_score 
            for cat, score in category_scores.items()
        }
        
        # 选择得分最高的分类
        best_category = max(category_scores.items(), key=lambda x: x[1])
        confidence = probabilities[best_category[0]]
        
        return ClassificationResult(
            category=best_category[0],
            confidence=confidence,
            probabilities=probabilities,
            method='keyword'
        )


class MLClassifier:
    """机器学习分类器"""
    
    def __init__(self, model_path: str = "models/classifier.pkl"):
        self.model_path = model_path
        self.model = None
        self.vectorizer = None
        self.label_map = {}
        self.text_preprocessor = TextPreprocessor()
        
        # 尝试加载已有模型
        self._load_model()
    
    def _load_model(self):
        """加载预训练模型"""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.model = data['model']
                    self.vectorizer = data['vectorizer']
                    self.label_map = data['label_map']
                logger.info("已加载预训练模型")
            except Exception as e:
                logger.warning(f"加载模型失败: {e}")
    
    def _save_model(self):
        """保存模型"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'vectorizer': self.vectorizer,
                'label_map': self.label_map
            }, f)
        logger.info("模型已保存")
    
    def train(self, texts: List[str], labels: List[str], 
              algorithm: str = 'naive_bayes', test_size: float = 0.2):
        """
        训练分类器
        
        Args:
            texts: 文本列表
            labels: 标签列表
            algorithm: 算法类型 ('naive_bayes', 'svm', 'random_forest')
            test_size: 测试集比例
        """
        logger.info(f"开始训练分类器，使用算法: {algorithm}")
        
        # 预处理文本
        processed_texts = [self.text_preprocessor.preprocess(text) for text in texts]
        
        # 创建标签映射
        unique_labels = list(set(labels))
        self.label_map = {i: label for i, label in enumerate(unique_labels)}
        reverse_label_map = {label: i for i, label in enumerate(unique_labels)}
        numeric_labels = [reverse_label_map[label] for label in labels]
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            processed_texts, numeric_labels, test_size=test_size, random_state=42
        )
        
        # 创建特征向量
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # 选择算法
        if algorithm == 'naive_bayes':
            self.model = MultinomialNB()
        elif algorithm == 'svm':
            self.model = SVC(probability=True, kernel='linear')
        elif algorithm == 'random_forest':
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"不支持的算法: {algorithm}")
        
        # 训练模型
        self.model.fit(X_train_vec, y_train)
        
        # 评估模型
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"模型训练完成，准确率: {accuracy:.4f}")
        
        # 打印分类报告
        target_names = [self.label_map[i] for i in range(len(unique_labels))]
        logger.info("\n" + classification_report(y_test, y_pred, target_names=target_names))
        
        # 保存模型
        self._save_model()
    
    def classify(self, text: str) -> ClassificationResult:
        """
        使用机器学习模型进行分类
        
        Args:
            text: 文本内容
            
        Returns:
            分类结果
        """
        if self.model is None or self.vectorizer is None:
            return ClassificationResult(
                category='life',
                confidence=0.0,
                probabilities={'life': 1.0},
                method='ml_not_trained'
            )
        
        # 预处理文本
        processed_text = self.text_preprocessor.preprocess(text)
        
        # 特征向量化
        X = self.vectorizer.transform([processed_text])
        
        # 预测
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        # 构建概率字典
        prob_dict = {
            self.label_map[i]: prob 
            for i, prob in enumerate(probabilities)
        }
        
        category = self.label_map[prediction]
        confidence = probabilities[prediction]
        
        return ClassificationResult(
            category=category,
            confidence=confidence,
            probabilities=prob_dict,
            method='ml'
        )


class SimilarityCalculator:
    """相似度计算器"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=1
        )
        self.text_preprocessor = TextPreprocessor()
        self.entries = {}
    
    def add_entry(self, entry_id: str, text: str):
        """
        添加条目到相似度索引
        
        Args:
            entry_id: 条目ID
            text: 文本内容
        """
        processed_text = self.text_preprocessor.preprocess(text)
        self.entries[entry_id] = processed_text
    
    def find_similar(self, text: str, top_k: int = 5) -> List[SimilarityResult]:
        """
        查找相似内容
        
        Args:
            text: 查询文本
            top_k: 返回最相似的K个结果
            
        Returns:
            相似度结果列表
        """
        if not self.entries:
            return []
        
        # 预处理查询文本
        processed_text = self.text_preprocessor.preprocess(text)
        
        # 构建语料库
        corpus = [processed_text] + list(self.entries.values())
        
        # 计算TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform(corpus)
        
        # 计算余弦相似度
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # 构建结果
        results = []
        entry_ids = list(self.entries.keys())
        
        for i, score in enumerate(similarities):
            if score > 0.1:  # 过滤低相似度
                results.append(SimilarityResult(
                    entry_id=entry_ids[i],
                    similarity_score=float(score),
                    content_preview=self.entries[entry_ids[i]][:100] + "..."
                ))
        
        # 排序并返回前K个
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]
    
    def check_duplicate(self, text: str, threshold: float = 0.85) -> Optional[SimilarityResult]:
        """
        检查是否重复
        
        Args:
            text: 文本内容
            threshold: 相似度阈值
            
        Returns:
            如果存在重复返回结果，否则None
        """
        similar = self.find_similar(text, top_k=1)
        
        if similar and similar[0].similarity_score >= threshold:
            return similar[0]
        
        return None


class ClassifierEngine:
    """分类引擎主类"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        
        # 初始化分类器
        self.keyword_classifier = KeywordClassifier()
        self.ml_classifier = MLClassifier()
        self.similarity_calculator = SimilarityCalculator()
        
        # 分类方法权重
        self.method_weights = {
            'keyword': 0.4,
            'ml': 0.6
        }
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置"""
        default_config = {
            'classification': {
                'auto_classify': True,
                'confidence_threshold': 0.6,
                'ml': {
                    'enabled': True,
                    'algorithm': 'naive_bayes'
                }
            }
        }
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    import yaml
                    config = yaml.safe_load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"加载配置失败: {e}")
        
        return default_config
    
    def classify(self, text: str, use_ml: bool = True) -> ClassificationResult:
        """
        综合分类
        
        Args:
            text: 文本内容
            use_ml: 是否使用机器学习
            
        Returns:
            分类结果
        """
        results = []
        
        # 关键词分类
        keyword_result = self.keyword_classifier.classify(text)
        results.append(('keyword', keyword_result))
        
        # 机器学习分类
        if use_ml and self.config['classification']['ml']['enabled']:
            ml_result = self.ml_classifier.classify(text)
            if ml_result.confidence > 0:
                results.append(('ml', ml_result))
        
        # 融合结果
        if len(results) == 1:
            return results[0][1]
        
        # 加权投票
        category_scores = defaultdict(float)
        
        for method, result in results:
            weight = self.method_weights.get(method, 0.5)
            for cat, prob in result.probabilities.items():
                category_scores[cat] += prob * weight
        
        # 选择最佳分类
        best_category = max(category_scores.items(), key=lambda x: x[1])
        total_score = sum(category_scores.values())
        
        probabilities = {
            cat: score / total_score 
            for cat, score in category_scores.items()
        }
        
        return ClassificationResult(
            category=best_category[0],
            confidence=probabilities[best_category[0]],
            probabilities=probabilities,
            method='ensemble'
        )
    
    def train_ml_model(self, texts: List[str], labels: List[str]):
        """
        训练机器学习模型
        
        Args:
            texts: 文本列表
            labels: 标签列表
        """
        algorithm = self.config['classification']['ml'].get('algorithm', 'naive_bayes')
        self.ml_classifier.train(texts, labels, algorithm=algorithm)
    
    def check_similarity(self, text: str, top_k: int = 5) -> List[SimilarityResult]:
        """
        检查相似内容
        
        Args:
            text: 文本内容
            top_k: 返回结果数量
            
        Returns:
            相似度结果列表
        """
        return self.similarity_calculator.find_similar(text, top_k)
    
    def check_duplicate(self, text: str, threshold: float = 0.85) -> Optional[SimilarityResult]:
        """
        检查是否重复
        
        Args:
            text: 文本内容
            threshold: 相似度阈值
            
        Returns:
            重复检测结果
        """
        return self.similarity_calculator.check_duplicate(text, threshold)
    
    def add_to_similarity_index(self, entry_id: str, text: str):
        """
        添加条目到相似度索引
        
        Args:
            entry_id: 条目ID
            text: 文本内容
        """
        self.similarity_calculator.add_entry(entry_id, text)


if __name__ == '__main__':
    # 测试代码
    engine = ClassifierEngine()
    
    # 测试分类
    test_texts = [
        "Python是一种强大的编程语言，适合数据分析和人工智能开发。",
        "今天学习了高等数学中的微积分，感觉很有趣。",
        "公司年会总结报告，今年的业绩增长了20%。",
        "周末去爬山，风景很美，空气很清新。",
        "股票投资策略分享，如何选择优质股票。",
        "健康饮食指南，多吃蔬菜水果有益身体。"
    ]
    
    print("=== 分类测试 ===")
    for text in test_texts:
        result = engine.classify(text, use_ml=False)
        print(f"\n文本: {text[:30]}...")
        print(f"分类: {result.category}, 置信度: {result.confidence:.2f}, 方法: {result.method}")
        print(f"概率分布: {result.probabilities}")
    
    # 测试相似度
    print("\n=== 相似度测试 ===")
    engine.add_to_similarity_index("1", "Python编程入门教程")
    engine.add_to_similarity_index("2", "Java开发指南")
    engine.add_to_similarity_index("3", "Python数据分析实战")
    
    similar = engine.check_similarity("Python编程学习")
    for result in similar:
        print(f"ID: {result.entry_id}, 相似度: {result.similarity_score:.2f}")
