"""
智能分类器引擎
==============

提供关键词匹配、语义相似度、多重分类和置信度评分功能。

Author: knowledge-converter
Version: 1.0.0
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from collections import Counter


@dataclass
class ClassificationResult:
    """分类结果"""
    category_id: str           # 分类ID
    category_name: str         # 分类名称
    document: str              # 目标文档
    confidence: float          # 置信度 (0-1)
    matched_keywords: List[str] = field(default_factory=list)  # 匹配的关键词
    match_type: str = "keyword"  # 匹配类型: keyword/semantic/fallback

    def __repr__(self):
        return (f"ClassificationResult("
                f"category={self.category_name}, "
                f"confidence={self.confidence:.2%}, "
                f"matches={self.matched_keywords})")


class ClassifierEngine:
    """
    智能分类器引擎

    功能特性:
    1. 关键词匹配: 提取内容关键词，与配置匹配
    2. 语义相似度: 使用 embedding 计算语义相似度（可选）
    3. 多重分类: 一张图片可属于多个分类
    4. 置信度评分: 返回置信度，高于阈值自动分类，低则人工确认

    使用示例:
        engine = ClassifierEngine()
        results = engine.classify("这是一篇关于抗炎饮食的文章")
        top_result = engine.suggest("宝宝辅食添加指南")
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        初始化分类器引擎

        Args:
            config_path: 分类配置文件路径，默认使用 config/categories.yaml
        """
        self.base_dir = Path(__file__).parent.parent
        self.config_path = config_path or self.base_dir / "config" / "categories.yaml"
        self.categories = []
        self.fallback_config = {}
        self.matching_config = {}
        self._load_config()

        # 语义相似度模型（延迟加载）
        self._semantic_model = None
        self._enable_semantic = False

    def _load_config(self):
        """加载配置文件"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self.categories = [
            cat for cat in config.get("categories", [])
            if cat.get("enabled", True)
        ]
        self.fallback_config = config.get("fallback", {})
        self.matching_config = config.get("matching", {})

    def reload_config(self):
        """重新加载配置"""
        self._load_config()

    def _normalize_text(self, text: str) -> str:
        """文本标准化"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符（保留中文、英文、数字）
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', ' ', text)
        return text.strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """提取文本关键词"""
        text = self._normalize_text(text)
        # 按空格分词
        words = text.split()
        # 过滤掉单字和常见停用词
        stop_words = {'的', '是', '在', '了', '和', '与', '或', '及', '等', '这', '那', '有', '没有'}
        words = [w for w in words if len(w) >= 2 and w not in stop_words]
        return words

    def _calculate_keyword_score(self, content: str, category: Dict) -> Tuple[float, List[str]]:
        """
        计算关键词匹配分数

        Returns:
            (score, matched_keywords): 分数和匹配的关键词列表
        """
        content_lower = content.lower()
        keywords = category.get("keywords", [])
        matched = []

        # 匹配模式
        mode = self.matching_config.get("mode", "any")
        case_sensitive = self.matching_config.get("case_sensitive", False)

        for keyword in keywords:
            if not case_sensitive:
                keyword_lower = keyword.lower()
            else:
                keyword_lower = keyword

            if keyword_lower in content_lower:
                matched.append(keyword)

        if not matched:
            return 0.0, []

        if mode == "all":
            # 全部匹配模式：分数 = 匹配数 / 总关键词数
            score = len(matched) / len(keywords) if keywords else 0
        else:
            # 任意匹配模式：分数 = 匹配数 / 5（归一化到0-1）
            score = min(len(matched) / 5.0, 1.0)

        return score, matched

    def _calculate_similarity(self, content: str, category: Dict) -> float:
        """
        计算语义相似度（如果启用）

        Args:
            content: 内容文本
            category: 分类配置

        Returns:
            相似度分数 (0-1)
        """
        if not self._enable_semantic or self._semantic_model is None:
            return 0.0

        try:
            # 获取分类的语义表示
            category_text = f"{category['name']} {category.get('description', '')}"
            category_text += " ".join(category.get("keywords", []))

            # 计算余弦相似度
            content_emb = self._semantic_model.encode([content])
            category_emb = self._semantic_model.encode([category_text])

            from sklearn.metrics.pairwise import cosine_similarity
            sim = cosine_similarity(content_emb, category_emb)[0][0]
            return float(sim)
        except Exception:
            return 0.0

    def _calculate_priority_boost(self, category: Dict) -> float:
        """计算优先级加成"""
        priority = category.get("priority", 5)
        # 将优先级(1-10)转换为加成(0-0.2)
        return (priority - 1) / 45 * 0.2

    def classify(
        self,
        content: str,
        threshold: float = 0.5,
        multi_class: bool = False,
        max_results: int = 3
    ) -> List[ClassificationResult]:
        """
        对内容进行分类

        Args:
            content: 待分类的内容文本
            threshold: 置信度阈值，低于此值的分类将被过滤
            multi_class: 是否返回多个分类结果
            max_results: 最大返回结果数（仅在 multi_class=True 时生效）

        Returns:
            分类结果列表，按置信度降序排列
        """
        if not content or not content.strip():
            return self._get_fallback_result()

        results = []

        for category in self.categories:
            # 1. 关键词匹配分数
            keyword_score, matched_keywords = self._calculate_keyword_score(content, category)

            # 2. 语义相似度分数（可选）
            semantic_score = self._calculate_similarity(content, category)

            # 3. 优先级加成
            priority_boost = self._calculate_priority_boost(category)

            # 4. 综合分数计算
            # 关键词匹配权重 0.7，语义相似度权重 0.3（如启用）
            if self._enable_semantic and semantic_score > 0:
                final_score = keyword_score * 0.7 + semantic_score * 0.3 + priority_boost
                match_type = "semantic" if semantic_score > keyword_score else "keyword"
            else:
                final_score = keyword_score + priority_boost
                match_type = "keyword" if keyword_score > 0 else "none"

            # 5. 检查是否达到阈值
            if final_score >= threshold or (match_type == "keyword" and keyword_score > 0):
                result = ClassificationResult(
                    category_id=category["id"],
                    category_name=category["name"],
                    document=category.get("document", ""),
                    confidence=min(final_score, 1.0),
                    matched_keywords=matched_keywords,
                    match_type=match_type
                )
                results.append(result)

        # 按置信度降序排列
        results.sort(key=lambda x: x.confidence, reverse=True)

        # 如果不是多分类模式，只返回最高置信度的结果
        if not multi_class and results:
            # 但如果最高置信度太低，返回 fallback
            if results[0].confidence < threshold * 0.5:
                return self._get_fallback_result()
            return [results[0]]

        # 限制返回数量
        return results[:max_results] if results else self._get_fallback_result()

    def suggest(self, content: str, top_k: int = 3) -> List[str]:
        """
        返回 Top-K 候选分类（简化版）

        Args:
            content: 待分类的内容文本
            top_k: 返回前 K 个候选

        Returns:
            分类ID列表
        """
        results = self.classify(content, threshold=0.1, multi_class=True, max_results=top_k)
        return [r.category_id for r in results]

    def _get_fallback_result(self) -> List[ClassificationResult]:
        """获取默认分类结果"""
        default_id = self.fallback_config.get("default_category_id", "misc")
        default_doc = self.fallback_config.get("default_document", "50_综合知识.md")

        return [ClassificationResult(
            category_id=default_id,
            category_name="综合知识",
            document=default_doc,
            confidence=0.3,
            matched_keywords=[],
            match_type="fallback"
        )]

    def enable_semantic(self, model_name: str = "text2vec-base-chinese"):
        """
        启用语义相似度功能

        Args:
            model_name: 模型名称
        """
        try:
            from sentence_transformers import SentenceTransformer
            self._semantic_model = SentenceTransformer(model_name)
            self._enable_semantic = True
            print(f"[ClassifierEngine] 语义相似度已启用，使用模型: {model_name}")
        except ImportError:
            print("[ClassifierEngine] 未安装 sentence-transformers，语义相似度功能不可用")
            print("[ClassifierEngine] 安装命令: pip install sentence-transformers")
        except Exception as e:
            print(f"[ClassifierEngine] 语义相似度启用失败: {e}")

    def disable_semantic(self):
        """禁用语义相似度功能"""
        self._enable_semantic = False
        self._semantic_model = None

    def get_categories(self) -> List[Dict]:
        """获取所有启用的分类"""
        return self.categories.copy()

    def get_category_info(self, category_id: str) -> Optional[Dict]:
        """获取指定分类的详细信息"""
        for cat in self.categories:
            if cat["id"] == category_id:
                return cat.copy()
        return None

    def explain_classification(self, content: str) -> Dict:
        """
        获取分类的详细解释

        Args:
            content: 内容文本

        Returns:
            包含详细分类信息的字典
        """
        results = self.classify(content, threshold=0.0, multi_class=True, max_results=5)

        explanation = {
            "input_length": len(content),
            "input_preview": content[:100] + "..." if len(content) > 100 else content,
            "categories": []
        }

        for r in results:
            cat_info = self.get_category_info(r.category_id)
            explanation["categories"].append({
                "id": r.category_id,
                "name": r.category_name,
                "confidence": r.confidence,
                "match_type": r.match_type,
                "matched_keywords": r.matched_keywords,
                "priority": cat_info.get("priority", 0) if cat_info else 0,
                "document": r.document
            })

        return explanation


def main():
    """命令行测试"""
    print("=" * 60)
    print("智能分类器引擎 - 测试")
    print("=" * 60)

    engine = ClassifierEngine()

    # 测试内容
    test_cases = [
        "抗炎饮食金字塔：每天摄入足够的Omega-3脂肪酸可以减少炎症反应",
        "宝宝6个月辅食添加指南，附详细食谱",
        "中医养生：春季养肝食谱推荐",
        "健身房器械使用教程，哑铃正确姿势",
        "旅游攻略：厦门三日游必去景点推荐",
        "益生菌对肠道健康的重要性",
        "家常菜谱：红烧肉的制作方法",
        "测试一下内容"
    ]

    print(f"\n发现 {len(engine.categories)} 个分类\n")

    for content in test_cases:
        print("-" * 50)
        print(f"内容: {content[:40]}...")
        results = engine.classify(content, threshold=0.3, multi_class=True)
        for i, r in enumerate(results[:3], 1):
            print(f"  [{i}] {r.category_name} (置信度: {r.confidence:.2%})")
            if r.matched_keywords:
                print(f"      匹配关键词: {', '.join(r.matched_keywords)}")
        print()


if __name__ == "__main__":
    main()
