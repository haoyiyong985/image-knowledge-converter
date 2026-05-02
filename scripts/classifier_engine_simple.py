#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版分类引擎 - 不依赖 sklearn
使用关键词匹配进行分类
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    category: str
    confidence: float
    probabilities: Dict[str, float]
    method: str


class SimpleClassifierEngine:
    """简化版分类引擎"""
    
    def __init__(self):
        # 分类体系 - 与 enhanced_batch_processor.py 保持一致
        self.categories = {
            "健康养生": {
                "keywords": ["健康", "养生", "医疗", "穴位", "中医", "食疗", "营养", "保健", "体检", "疾病", "治疗", "药品", "草药", "低密度脂蛋白", "清热解毒",
                           "抗炎", "坚果", "ω-6", "ω-3", "ORAC", "抗氧化", "膳食纤维", "营养素", "食物成分", "羽衣甘蓝", "轻食",
                           "脂肪酸", "反式脂肪", "饱和脂肪", "不饱和脂肪", "胆固醇", "血糖", "血脂", "血压",
                           "维生素", "矿物质", "蛋白质", "碳水化合物", "热量", "卡路里", "代谢", "内分泌",
                           "炎症", "氧化应激", "自由基", "免疫力", "体质"],
                "doc_file": "01_抗炎饮食与营养科普.md"
            },
            "肠道健康": {
                "keywords": ["肠道", "益生菌", "益生元", "绿灯食物", "红灯食物", "黄灯食物", "微生物", "膳食纤维", "控糖",
                           "便秘", "腹泻", "消化", "吸收", "菌群", "胃部", "胃炎", "胃溃疡", "肠炎",
                           "排毒", "清肠", "通便", "润肠", "肠胃", "脾胃", "幽门螺杆菌"],
                "doc_file": "02_肠道健康与饮食分类.md"
            },
            "中医养生": {
                "keywords": ["中医", "三伏", "养生", "食疗", "茶饮", "汤药", "湿气", "健脾", "温补", "穴位", "经络",
                           "气血", "阴阳", "五行", "脏腑", "肝火", "肾虚", "脾虚", "肺热", "心寒",
                           "滋补", "调理", "养生茶", "药膳", "食补", "食疗方", "传统医学", "本草纲目",
                           "艾灸", "拔罐", "刮痧", "按摩", "推拿", "针灸", "足疗"],
                "doc_file": "03_中医养生与食疗.md"
            },
            "日常饮食": {
                "keywords": ["早餐", "食谱", "搭配", "热量", "蛋白质", "减脂", "饮食建议", "营养", "食物", "膳食", "宝塔", "脂肪肝",
                           "午餐", "晚餐", "加餐", "零食", "饮品", "烹饪", "做法", "食材", "选购",
                           "减肥", "瘦身", "增肌", "健身", "运动", "饮食习惯", "饮食禁忌", "食物搭配",
                           "家常菜", "快手菜", "简单料理", "懒人食谱", "一人食", "便当"],
                "doc_file": "04_日常饮食建议.md"
            }
        }
    
    def classify(self, text: str):
        """
        对文本进行分类
        
        Args:
            text: 待分类文本
            
        Returns:
            ClassificationResult 对象
        """
        if not text:
            return ClassificationResult("未知", 0.0, {}, "keyword")
        
        text = text.lower()
        scores = {}
        
        for category, info in self.categories.items():
            score = 0
            for keyword in info["keywords"]:
                count = text.count(keyword.lower())
                score += count
            
            # 归一化
            if len(info["keywords"]) > 0:
                scores[category] = score / len(info["keywords"])
            else:
                scores[category] = 0
        
        # 找出最高分
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            
            # 如果所有分数都很低，默认归入健康养生（与1.0版本保持一致）
            if best_score < 0.05:
                return ClassificationResult("健康养生", 0.3, scores, "keyword")
            
            return ClassificationResult(best_category, min(best_score, 1.0), scores, "keyword")
        
        return ClassificationResult("未知", 0.0, {}, "keyword")
    
    def get_category_doc(self, category: str) -> str:
        """获取分类对应的文档名"""
        if category in self.categories:
            return category + ".md"
        return None
    
    def extract_title(self, text: str) -> str:
        """提取标题"""
        lines = text.strip().split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50:
                return line
        return "未命名章节"


# 保持向后兼容
ClassifierEngine = SimpleClassifierEngine


if __name__ == "__main__":
    # 测试
    engine = SimpleClassifierEngine()
    
    test_texts = [
        "三伏天养生要先清后补，可以食用苦瓜、丝瓜、冬瓜",
        "坚果的ω-6与ω-3比例很重要，亚麻籽比例优秀",
        "早餐建议吃全麦吐司、煮鸡蛋、新鲜浆果",
        "绿灯食物推荐大量食用，如洋葱、大蒜、豆类"
    ]
    
    for text in test_texts:
        category, confidence = engine.classify(text)
        print(f"文本: {text[:30]}...")
        print(f"分类: {category} (置信度: {confidence:.2f})")
        print()
