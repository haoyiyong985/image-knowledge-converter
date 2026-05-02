#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片分类引擎
============
基于关键词匹配的图片内容分类器
支持可配置的分类规则 YAML
支持自动识别未知内容并新增分类

使用方式：
    from image_classifier import ImageClassifier
    
    classifier = ImageClassifier()
    result = classifier.classify("图片识别出的文字内容")
    print(f"分类: {result['category']}, 置信度: {result['confidence']}")
"""

import os
import re
import yaml
import logging
import unicodedata
from collections import Counter
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 通用停用词（不作为主题关键词）
STOP_WORDS = {
    '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个',
    '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好',
    '这', '那', '里', '来', '他', '她', '它', '我们', '你们', '他们', '什么', '这个',
    '因为', '所以', '但是', '如果', '虽然', '然后', '可以', '这样', '那么', '只是',
    '可能', '非常', '已经', '还是', '还有', '以及', '或者', '而且', '时候', '这些',
    '那些', '需要', '进行', '方法', '使用', '注意', '内容', '情况', '问题', '作用',
    '功能', '效果', '影响', '发现', '感觉', '时间', '出现', '减少', '增加', '促进',
    '帮助', '改善', '通过', '保持', '同时', '包括', '提高', '补充', '加入', '食物',
    '每天', '每日', '适量', '建议', '尽量', '注意', '必须', '不要', '不能', '应该',
    '能够', '可能', '左右', '以上', '以下', '之间', '相关', '主要', '一般', '特别',
    '研究', '显示', '表明', '认为', '发现', '指出', '报道',
}


@dataclass
class CategoryMatch:
    """分类匹配结果"""
    category_id: str
    category_name: str
    matched_keywords: List[str]
    match_count: int
    confidence: float
    priority: int
    document: str


class ImageClassifier:
    """
    图片内容分类器
    
    通过关键词匹配识别图片内容所属分类
    支持 YAML 配置文件，用户可自定义分类规则
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化分类器
        
        Args:
            config_path: 分类配置文件路径
        """
        if config_path is None:
            base_dir = Path("D:/新建文件夹")
            config_path = base_dir / "config" / "categories.yaml"
        
        self.config_path = Path(config_path)
        self.config: Dict = {}
        self.categories: List[Dict] = []
        self.fallback: Dict = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载分类配置"""
        if not self.config_path.exists():
            logger.warning(f"配置文件不存在: {self.config_path}")
            logger.info("将使用内置默认配置")
            self._load_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            self.categories = [c for c in self.config.get('categories', []) if c.get('enabled', True)]
            self.fallback = self.config.get('fallback', {})
            
            logger.info(f"[OK] 已加载 {len(self.categories)} 个分类配置")
            
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """加载默认配置"""
        self.categories = [
            {
                'id': 'nutrition',
                'name': '营养科普',
                'keywords': ['抗炎', '营养素', '维生素', '抗氧化', '蛋白质'],
                'priority': 10,
                'document': '01_抗炎饮食与营养科普.md'
            },
            {
                'id': 'gut_health',
                'name': '肠道健康',
                'keywords': ['益生菌', '膳食纤维', '消化', '肠道'],
                'priority': 9,
                'document': '02_肠道健康与饮食分类.md'
            },
            {
                'id': 'tcm',
                'name': '中医养生',
                'keywords': ['食疗', '中医', '体质', '药膳', '经络'],
                'priority': 9,
                'document': '03_中医养生与食疗.md'
            },
            {
                'id': 'parenting',
                'name': '育儿知识',
                'keywords': ['宝宝', '辅食', '育儿', '孕妇'],
                'priority': 8,
                'document': '47_宝宝辅食与育儿.md'
            },
            {
                'id': 'daily_diet',
                'name': '日常饮食',
                'keywords': ['食谱', '做法', '烹饪', '食材'],
                'priority': 7,
                'document': '04_日常饮食建议.md'
            },
            {
                'id': 'misc',
                'name': '综合知识',
                'keywords': [],
                'priority': 0,
                'document': '50_综合知识.md'
            }
        ]
        self.fallback = {
            'default_category_id': 'misc',
            'default_document': '50_综合知识.md',
            'min_confidence': 0.3
        }
        logger.info("[OK] 已加载默认分类配置")
    
    def reload_config(self):
        """重新加载配置（修改配置后调用）"""
        self._load_config()
    
    def _count_keyword_matches(self, text: str, keywords: List[str], 
                                case_sensitive: bool = False) -> tuple:
        """
        统计关键词匹配数量
        
        Returns:
            (匹配数量, 匹配的关键词列表)
        """
        if not case_sensitive:
            text_lower = text.lower()
            kw_list = [k.lower() for k in keywords]
        else:
            text_lower = text
            kw_list = keywords
        
        matched = []
        for kw in kw_list:
            if kw in text_lower:
                matched.append(kw)
        
        return len(matched), matched
    
    def classify(self, text: str, return_all: bool = False) -> Dict:
        """
        对文本内容进行分类
        
        Args:
            text: 待分类的文本（通常是 OCR 识别结果）
            return_all: 是否返回所有匹配结果
            
        Returns:
            分类结果字典
        """
        if not text or not text.strip():
            return self._get_fallback_result("空内容")
        
        # 清理文本
        text_clean = re.sub(r'\s+', '', text)
        
        matching_config = self.config.get('matching', {})
        case_sensitive = matching_config.get('case_sensitive', False)
        
        # 匹配所有分类
        matches: List[CategoryMatch] = []
        
        for category in self.categories:
            keywords = category.get('keywords', [])
            if not keywords:
                continue
            
            match_count, matched_keywords = self._count_keyword_matches(
                text_clean, keywords, case_sensitive
            )
            
            if match_count > 0:
                # 计算置信度：基于匹配数量和优先级
                priority = category.get('priority', 1)
                # 归一化置信度 = 匹配数 / (总关键词数 * 0.3) 并加权优先级
                if len(keywords) > 0:
                    base_confidence = match_count / len(keywords)
                    confidence = min(base_confidence * 0.5 + (priority / 20), 1.0)
                else:
                    confidence = 0.5
                
                matches.append(CategoryMatch(
                    category_id=category['id'],
                    category_name=category.get('name', category['id']),
                    matched_keywords=matched_keywords,
                    match_count=match_count,
                    confidence=confidence,
                    priority=priority,
                    document=category.get('document', '')
                ))
        
        if not matches:
            return self._get_fallback_result("无匹配分类")
        
        # 按置信度排序
        matches.sort(key=lambda x: (x.confidence, x.priority), reverse=True)
        
        # 获取最佳匹配
        best = matches[0]
        min_confidence = self.fallback.get('min_confidence', 0.3)
        
        if best.confidence < min_confidence:
            return self._get_fallback_result(f"置信度不足 ({best.confidence:.2f})", best)
        
        result = {
            'success': True,
            'category_id': best.category_id,
            'category_name': best.category_name,
            'confidence': best.confidence,
            'matched_keywords': best.matched_keywords,
            'match_count': best.match_count,
            'document': best.document,
            'message': f"分类为 {best.category_name}，置信度 {best.confidence:.1%}"
        }
        
        if return_all:
            result['all_matches'] = [
                {
                    'category_id': m.category_id,
                    'category_name': m.category_name,
                    'confidence': m.confidence,
                    'match_count': m.match_count,
                    'matched_keywords': m.matched_keywords
                }
                for m in matches[:5]  # 最多返回前5个
            ]
        
        return result
    
    def _get_fallback_result(self, reason: str, best_match: CategoryMatch = None) -> Dict:
        """获取默认分类结果"""
        default_id = self.fallback.get('default_category_id', 'misc')
        default_doc = self.fallback.get('default_document', '50_综合知识.md')
        
        # 尝试从配置中获取默认分类名称
        default_name = default_id
        for cat in self.categories:
            if cat.get('id') == default_id:
                default_name = cat.get('name', default_id)
                break
        
        result = {
            'success': True,
            'category_id': default_id,
            'category_name': default_name,
            'confidence': 0.0,
            'matched_keywords': [],
            'match_count': 0,
            'document': default_doc,
            'message': f"使用默认分类 ({reason})"
        }
        
        # 如果有较接近的匹配，添加提示
        if best_match and best_match.confidence > 0:
            result['suggestion'] = {
                'category_id': best_match.category_id,
                'category_name': best_match.category_name,
                'confidence': best_match.confidence,
                'reason': '置信度低于阈值'
            }
        
        return result
    
    def classify_batch(self, texts: List[str]) -> List[Dict]:
        """
        批量分类
        
        Args:
            texts: 文本列表
            
        Returns:
            分类结果列表
        """
        return [self.classify(text) for text in texts]
    
    def get_categories(self) -> List[Dict]:
        """获取所有分类配置"""
        return [
            {
                'id': c.get('id'),
                'name': c.get('name'),
                'description': c.get('description', ''),
                'keywords_count': len(c.get('keywords', [])),
                'priority': c.get('priority', 0),
                'enabled': c.get('enabled', True)
            }
            for c in self.categories
        ]
    
    def get_category_by_id(self, category_id: str) -> Optional[Dict]:
        """根据ID获取分类配置"""
        for cat in self.categories:
            if cat.get('id') == category_id:
                return cat
        return None

    # ============================================================
    # 自动新增分类功能
    # ============================================================

    def _extract_topic_keywords(self, text: str, top_n: int = 15) -> List[str]:
        """
        从文本中提取主题关键词
        
        策略：
        1. 提取2-6字的中文词组（高频词优先）
        2. 过滤停用词
        3. 优先保留名词性词组
        
        Returns:
            候选关键词列表（按频率降序）
        """
        # 提取所有2-6字的中文词组
        candidates = re.findall(r'[\u4e00-\u9fff]{2,6}', text)
        
        # 过滤停用词
        filtered = [w for w in candidates if w not in STOP_WORDS and len(w) >= 2]
        
        # 统计频次
        counter = Counter(filtered)
        
        # 取高频词
        top_words = [w for w, _ in counter.most_common(top_n * 2)]
        
        # 进一步过滤：去掉纯数字、太通用的词
        final = []
        for w in top_words:
            if len(final) >= top_n:
                break
            if w not in STOP_WORDS:
                final.append(w)
        
        return final

    def _generate_category_id(self, name: str) -> str:
        """
        根据分类名称生成唯一 ID
        使用拼音首字母 + 时间戳后缀
        """
        import time
        # 去除非字母数字字符，转小写
        safe_name = re.sub(r'[^\w]', '', name, flags=re.UNICODE)
        # 取前6个字（中文用unicode范围）
        cn_chars = re.findall(r'[\u4e00-\u9fff]', safe_name)[:4]
        timestamp = str(int(time.time()))[-5:]
        # 用字符个数+时间戳组合
        return f"auto_{len(cn_chars)}c_{timestamp}"

    def _infer_category_name(self, keywords: List[str], text: str) -> Tuple[str, str]:
        """
        根据关键词推断分类名称和文档名
        
        Returns:
            (category_name, document_name)
        """
        # 取前2个高频关键词作为分类名
        if len(keywords) >= 2:
            name = f"{keywords[0]}{keywords[1]}类"
        elif len(keywords) == 1:
            name = f"{keywords[0]}类"
        else:
            name = "未知分类"
        
        # 生成文档名（用序号+名称）
        doc_num = self._get_next_doc_number()
        doc_name = f"{doc_num:02d}_{name}.md"
        
        return name, doc_name

    def _get_next_doc_number(self) -> int:
        """获取下一个可用的文档序号"""
        max_num = 50
        for cat in self.categories:
            doc = cat.get('document', '')
            m = re.match(r'^(\d+)_', doc)
            if m:
                num = int(m.group(1))
                if num > max_num:
                    max_num = num
        return max_num + 1

    def auto_add_category(self, text: str, category_name: str = None,
                          keywords: List[str] = None, document: str = None,
                          priority: int = 5, description: str = None) -> Dict:
        """
        根据文本内容自动分析并添加新分类到配置文件
        
        Args:
            text: 触发新增的文本内容
            category_name: 手动指定分类名（可选，不填则自动推断）
            keywords: 手动指定关键词（可选，不填则自动提取）
            document: 手动指定文档名（可选）
            priority: 优先级（默认5）
            description: 分类描述（可选）
            
        Returns:
            {
                'success': bool,
                'category_id': str,
                'category_name': str,
                'keywords': list,
                'document': str,
                'message': str
            }
        """
        # 1. 提取关键词
        if not keywords:
            keywords = self._extract_topic_keywords(text, top_n=12)
        
        if len(keywords) < 2:
            return {
                'success': False,
                'message': '关键词不足，无法创建新分类（需要至少2个）',
                'keywords': keywords
            }
        
        # 2. 推断分类名和文档名
        if not category_name:
            category_name, auto_doc = self._infer_category_name(keywords, text)
        else:
            auto_doc = None
        
        if not document:
            document = auto_doc or f"{self._get_next_doc_number():02d}_{category_name}.md"
        
        if not description:
            description = f"自动创建：{', '.join(keywords[:5])}"
        
        # 3. 生成唯一 ID
        category_id = self._generate_category_id(category_name)
        
        # 4. 检查是否已有同名分类
        for cat in self.categories:
            if cat.get('name') == category_name:
                # 已存在同名，追加关键词
                return self._merge_keywords_to_existing(cat, keywords)
        
        # 5. 构建新分类配置
        new_category = {
            'id': category_id,
            'name': category_name,
            'keywords': keywords,
            'priority': priority,
            'document': document,
            'enabled': True,
            'description': description,
            'auto_created': True,
        }
        
        # 6. 写入 YAML
        success = self._append_category_to_yaml(new_category)
        
        if success:
            # 热更新内存中的分类列表
            self.categories.append(new_category)
            logger.info(f"[NEW] 自动新增分类: {category_name} (ID: {category_id})")
            return {
                'success': True,
                'category_id': category_id,
                'category_name': category_name,
                'keywords': keywords,
                'document': document,
                'message': f"已自动创建新分类 [{category_name}]，关键词 {len(keywords)} 个"
            }
        else:
            return {
                'success': False,
                'message': '写入配置文件失败，请检查文件权限',
                'category_name': category_name,
                'keywords': keywords
            }

    def _merge_keywords_to_existing(self, cat: Dict, new_keywords: List[str]) -> Dict:
        """
        向已有分类追加新关键词（去重）
        """
        existing_kws = set(cat.get('keywords', []))
        added = [kw for kw in new_keywords if kw not in existing_kws]
        
        if not added:
            return {
                'success': True,
                'category_id': cat['id'],
                'category_name': cat['name'],
                'keywords': cat.get('keywords', []),
                'document': cat.get('document', ''),
                'message': f"分类 [{cat['name']}] 已存在，关键词无变化"
            }
        
        # 更新内存
        cat['keywords'] = list(existing_kws) + added
        
        # 写回 YAML
        self._save_config()
        
        logger.info(f"[UPDATE] 向分类 [{cat['name']}] 追加 {len(added)} 个关键词: {added}")
        return {
            'success': True,
            'category_id': cat['id'],
            'category_name': cat['name'],
            'keywords': cat['keywords'],
            'document': cat.get('document', ''),
            'message': f"分类 [{cat['name']}] 已存在，新增关键词 {len(added)} 个: {added}"
        }

    def _append_category_to_yaml(self, new_category: Dict) -> bool:
        """
        将新分类追加到 YAML 配置文件
        保留原有格式，仅在 categories 末尾追加
        """
        try:
            if not self.config_path.exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return False
            
            # 读取现有配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw = f.read()
            
            # 构建追加内容（手动格式化以保持可读性）
            kw_lines = '\n'.join(f'      - "{kw}"' for kw in new_category['keywords'])
            block = f"""
  # ============ 自动新增分类 ============
  - id: "{new_category['id']}"
    name: "{new_category['name']}"
    keywords:
{kw_lines}
    priority: {new_category['priority']}
    document: "{new_category['document']}"
    enabled: true
    description: "{new_category['description']}"
    auto_created: true
"""
            # 找到 fallback 节点前插入
            if '\nfallback:' in raw:
                insert_pos = raw.index('\nfallback:')
                new_raw = raw[:insert_pos] + block + raw[insert_pos:]
            else:
                new_raw = raw + block
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                f.write(new_raw)
            
            return True
        except Exception as e:
            logger.error(f"追加分类到 YAML 失败: {e}")
            return False

    def _save_config(self) -> bool:
        """
        将当前内存中的 categories 完整写回 YAML
        （用于关键词合并场景）
        """
        try:
            if not self.config_path.exists():
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            config['categories'] = self.categories
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False,
                          sort_keys=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False

    def classify_with_auto_add(self, text: str, auto_add_threshold: float = 0.2,
                                min_text_length: int = 30) -> Dict:
        """
        分类 + 自动新增功能的一体化接口
        
        当置信度低于 auto_add_threshold 时，自动提取主题并新增分类。
        
        Args:
            text: 待分类文本
            auto_add_threshold: 触发自动新增的最低置信度阈值（默认0.2）
            min_text_length: 触发自动新增所需的最短文本长度（避免对短文本乱加）
            
        Returns:
            分类结果字典，新增字段:
            - auto_added: bool  是否触发了自动新增
            - auto_add_result: dict  新增结果详情（仅在 auto_added=True 时存在）
        """
        result = self.classify(text, return_all=True)
        result['auto_added'] = False
        
        confidence = result.get('confidence', 0.0)
        text_len = len(text.strip())
        
        # 判断是否需要自动新增
        should_auto_add = (
            confidence < auto_add_threshold
            and text_len >= min_text_length
            and result.get('category_id') in (
                self.fallback.get('default_category_id', 'misc'), None
            )
        )
        
        if should_auto_add:
            logger.info(f"置信度 {confidence:.1%} < 阈值 {auto_add_threshold:.1%}，"
                        f"触发自动新增分类（文本长度: {text_len}）")
            
            add_result = self.auto_add_category(text)
            result['auto_added'] = add_result.get('success', False)
            result['auto_add_result'] = add_result
            
            if add_result.get('success'):
                # 用新分类重新分类
                reclassify = self.classify(text)
                if reclassify.get('confidence', 0) > confidence:
                    # 新分类更好，更新结果
                    result.update({
                        'category_id': reclassify['category_id'],
                        'category_name': reclassify['category_name'],
                        'confidence': reclassify['confidence'],
                        'matched_keywords': reclassify['matched_keywords'],
                        'document': reclassify['document'],
                        'message': f"[自动新增] {reclassify['message']}",
                    })
        
        return result


# ============================================================
# 命令行工具
# ============================================================

def cmd_test_auto():
    """测试自动新增分类功能"""
    import time
    
    # 使用全新的测试配置（不污染主配置）
    test_config_path = Path("D:/新建文件夹/config/categories_test.yaml")
    
    # 复制主配置作为测试配置
    src = Path("D:/新建文件夹/config/categories.yaml")
    if src.exists():
        import shutil
        shutil.copy(src, test_config_path)
        print(f"[INFO] 使用测试配置: {test_config_path.name}")
    
    classifier = ImageClassifier(config_path=str(test_config_path))
    
    # 测试场景1：完全陌生的内容（汽车保养）
    unknown_text_1 = """
    汽车保养小知识：机油更换周期一般是5000公里或半年，具体看机油型号。
    轮胎气压需要定期检查，一般2.2-2.5bar。刹车片磨损到警告线需要立即更换。
    空调滤芯建议每年更换一次。变速箱油大约每4万公里更换。
    火花塞一般10万公里更换。冷却液每两年更换一次。
    """
    
    # 测试场景2：宠物护理
    unknown_text_2 = """
    狗狗每天需要喝足够的水，成年犬每公斤体重需要60ml水。
    猫咪洗澡频率不宜过高，一般1-2个月一次。宠物猫需要定期驱虫、打疫苗。
    狗粮选择要看蛋白质含量，最好在25%以上。猫粮要注意磷含量不能太高。
    宠物换毛期需要每天梳毛，防止毛发打结。
    """
    
    # 测试场景3：接近已有分类但置信度低的内容（股票理财）
    borderline_text = """
    股票投资要分散风险，不要把所有钱放在一只股票上。
    基金定投可以降低成本，适合普通投资者。理财要做好风险评估。
    """
    
    print("\n" + "=" * 60)
    print("自动新增分类功能测试")
    print("=" * 60)
    
    # --- 测试1: classify_with_auto_add 一体化接口 ---
    print("\n[测试1] 汽车保养类内容（完全陌生）")
    result1 = classifier.classify_with_auto_add(unknown_text_1, auto_add_threshold=0.25)
    print(f"  原始分类: {result1['category_name']} (置信度: {result1['confidence']:.1%})")
    print(f"  自动新增: {result1['auto_added']}")
    if result1.get('auto_add_result'):
        ar = result1['auto_add_result']
        print(f"  新增结果: {ar['message']}")
        if ar.get('keywords'):
            print(f"  提取关键词: {', '.join(ar['keywords'][:8])}")
    
    # --- 测试2: 直接 auto_add_category 手动触发 ---
    print("\n[测试2] 宠物护理类内容（手动触发）")
    result2 = classifier.auto_add_category(unknown_text_2, category_name="宠物护理")
    print(f"  结果: {result2['message']}")
    if result2.get('keywords'):
        print(f"  关键词: {', '.join(result2['keywords'][:8])}")
    
    # --- 测试3: 重新加载后验证持久化 ---
    print("\n[测试3] 验证持久化 - 重新加载配置")
    classifier2 = ImageClassifier(config_path=str(test_config_path))
    cats = classifier2.get_categories()
    auto_cats = [c for c in cats if '自动' in c.get('description', '') or c.get('id', '').startswith('auto_')]
    print(f"  配置文件分类总数: {len(cats)}")
    print(f"  自动新增分类数: {len(auto_cats)}")
    for c in auto_cats:
        print(f"    - [{c['name']}] {c['keywords_count']} 个关键词")
    
    # --- 测试4: 对同名分类追加关键词 ---
    print("\n[测试4] 向已有分类追加关键词")
    extra_text = "狗狗打疫苗是必须的，每年需要注射狂犬病疫苗，还有五联苗六联苗"
    result4 = classifier2.auto_add_category(extra_text, category_name="宠物护理")
    print(f"  结果: {result4['message']}")
    
    # 清理测试配置
    if test_config_path.exists():
        test_config_path.unlink()
        print("\n[INFO] 测试配置已清理")
    
    print("\n[DONE] 自动新增分类功能测试完成")


def cmd_auto_add(text: str = None, file: str = None, name: str = None):
    """命令行：自动新增分类"""
    classifier = ImageClassifier()
    
    if file:
        if not os.path.exists(file):
            print(f"[ERROR] 文件不存在: {file}")
            return
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
    
    if not text:
        print("[ERROR] 请提供文本内容")
        print("用法: python image_classifier.py auto-add --text '文本内容'")
        return
    
    result = classifier.auto_add_category(text, category_name=name)
    
    print("\n" + "=" * 60)
    print("自动新增分类结果")
    print("=" * 60)
    if result['success']:
        print(f"[OK] {result['message']}")
        print(f"分类ID: {result['category_id']}")
        print(f"分类名: {result['category_name']}")
        print(f"文档:   {result['document']}")
        print(f"关键词 ({len(result['keywords'])} 个): {', '.join(result['keywords'][:8])}")
    else:
        print(f"[FAIL] {result['message']}")
        if result.get('keywords'):
            print(f"提取到的关键词: {result['keywords']}")


def cmd_classify(text: str = None, file: str = None):
    """命令行分类"""
    classifier = ImageClassifier()
    
    if file:
        # 从文件读取文本
        if not os.path.exists(file):
            print(f"[ERROR] 文件不存在: {file}")
            return
        
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"从文件读取文本，长度: {len(text)} 字符")
    
    if not text:
        print("[ERROR] 请提供要分类的文本内容")
        print("用法: python image_classifier.py --text '文本内容'")
        print("      python image_classifier.py --file result.txt")
        return
    
    result = classifier.classify(text, return_all=True)
    
    print("\n" + "=" * 60)
    print("分类结果")
    print("=" * 60)
    print(f"分类: {result['category_name']} ({result['category_id']})")
    print(f"置信度: {result['confidence']:.1%}")
    print(f"文档: {result['document']}")
    print(f"原因: {result['message']}")
    
    if result.get('matched_keywords'):
        print(f"\n匹配关键词 ({len(result['matched_keywords'])}/{result['match_count']}):")
        for kw in result['matched_keywords'][:10]:
            print(f"  - {kw}")
    
    if result.get('all_matches'):
        print("\n其他候选分类:")
        for i, m in enumerate(result['all_matches'][1:4], 1):
            print(f"  {i}. {m['category_name']} ({m['confidence']:.1%})")


def cmd_list():
    """列出所有分类"""
    classifier = ImageClassifier()
    categories = classifier.get_categories()
    
    print("\n" + "=" * 60)
    print(f"分类列表 (共 {len(categories)} 个)")
    print("=" * 60)
    
    for cat in sorted(categories, key=lambda x: x['priority'], reverse=True):
        status = "[启用]" if cat['enabled'] else "[禁用]"
        print(f"\n{status} {cat['name']} ({cat['id']})")
        print(f"   描述: {cat['description']}")
        print(f"   关键词: {cat['keywords_count']} 个 | 优先级: {cat['priority']}")


def cmd_test():
    """测试分类功能"""
    classifier = ImageClassifier()
    
    test_cases = [
        ("抗炎饮食要多吃这些食物，补充维生素和膳食纤维", "营养科普"),
        ("中医教你如何调理脾胃，祛湿补气血", "中医养生"),
        ("宝宝辅食添加要注意什么？育儿专家告诉你", "育儿知识"),
        ("益生菌对肠道健康有什么好处？", "肠道健康"),
        ("今天做了红烧肉，做法很简单", "日常饮食"),
    ]
    
    print("\n" + "=" * 60)
    print("分类功能测试")
    print("=" * 60)
    
    correct = 0
    for text, expected in test_cases:
        result = classifier.classify(text)
        status = "[OK]" if result['category_name'] == expected else "[FAIL]"
        if result['category_name'] == expected:
            correct += 1
        print(f"\n{status} 文本: {text[:30]}...")
        print(f"    预期: {expected}")
        print(f"    实际: {result['category_name']} ({result['confidence']:.1%})")
    
    print(f"\n准确率: {correct}/{len(test_cases)} ({correct/len(test_cases):.0%})")


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("图片分类器 - 命令行工具")
        print("")
        print("用法:")
        print("  python image_classifier.py classify --text '文本内容'")
        print("  python image_classifier.py classify --file result.txt")
        print("  python image_classifier.py auto-add --text '新内容'     # 自动新增分类")
        print("  python image_classifier.py auto-add --text '...' --name '自定义名称'")
        print("  python image_classifier.py list")
        print("  python image_classifier.py test")
        print("  python image_classifier.py test-auto                    # 测试自动新增功能")
        return
    
    command = sys.argv[1]
    
    if command == "classify":
        text = None
        file = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--text" and i + 1 < len(args):
                text = args[i + 1]
                i += 2
            elif args[i] == "--file" and i + 1 < len(args):
                file = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_classify(text=text, file=file)
    
    elif command == "auto-add":
        text = None
        file = None
        name = None
        args = sys.argv[2:]
        i = 0
        while i < len(args):
            if args[i] == "--text" and i + 1 < len(args):
                text = args[i + 1]
                i += 2
            elif args[i] == "--file" and i + 1 < len(args):
                file = args[i + 1]
                i += 2
            elif args[i] == "--name" and i + 1 < len(args):
                name = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_auto_add(text=text, file=file, name=name)
    
    elif command == "list":
        cmd_list()
    
    elif command == "test":
        cmd_test()
    
    elif command == "test-auto":
        cmd_test_auto()
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
