#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版分批图片处理器 v2.0
==========================

核心优化：
  1. 智能分批策略（按图片大小动态调整批次）
  2. 并发OCR处理（多线程+引擎池）
  3. 内存监控与自动GC
  4. 重复内容实时检测
  5. 引擎自动降级与恢复
  6. 详细性能统计与报告

批次策略：
  - 小图(<500KB)：20-30张/批
  - 中图(500KB-2MB)：10-15张/批  
  - 大图(>2MB)：5-8张/批
  - 超大图(>5MB)：3-5张/批
"""

import os
import sys
import json
import shutil
import time
import gc
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import logging

# 先配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入现有模块
try:
    from ocr_manager import OCRManager, OCREngine
    # 尝试导入完整版分类器，失败则使用简化版
    try:
        from classifier_engine import ClassifierEngine
    except ImportError:
        from classifier_engine_simple import SimpleClassifierEngine as ClassifierEngine
        logger.info("[INFO] 使用简化版分类引擎")
except ImportError as e:
    print(f"[ERROR] 缺少依赖模块: {e}")
    sys.exit(1)

# ============================================================
# 配置
# ============================================================
BASE_DIR = Path("D:/新建文件夹")
PENDING_DIR = BASE_DIR / "待处理图片"
PROCESSED_DIR = BASE_DIR / "已处理图片"
RESULT_DIR = BASE_DIR / "处理结果"
PROGRESS_DIR = BASE_DIR / "progress"
LOGS_DIR = BASE_DIR / "logs"

# 创建必要目录
for dir_path in [PROGRESS_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# 智能分批配置
BATCH_CONFIG = {
    "small": {"max_size": 500 * 1024, "batch_size": 25},      # <500KB
    "medium": {"max_size": 2 * 1024 * 1024, "batch_size": 12}, # 500KB-2MB
    "large": {"max_size": 5 * 1024 * 1024, "batch_size": 6},   # 2MB-5MB
    "xlarge": {"max_size": float('inf'), "batch_size": 3},     # >5MB
}

# 并发配置
MAX_WORKERS = 3          # 最大并发工作线程
ENGINE_COOLDOWN = 2      # 引擎冷却时间（秒）
BATCH_INTERVAL = 1       # 批次间隔（秒）
MEMORY_THRESHOLD = 80    # 内存使用率阈值（%）

# 分类体系（与原有保持一致）
CATEGORIES = {
    "健康养生": {
        "keywords": ["健康", "养生", "医疗", "穴位", "中医", "食疗", "营养", "保健", "体检", "疾病", "治疗", "药品", "草药", "低密度脂蛋白", "清热解毒"],
        "doc_file": "01_抗炎饮食与营养科普.md"
    },
    "肠道健康": {
        "keywords": ["肠道", "益生菌", "益生元", "绿灯食物", "红灯食物", "微生物", "膳食纤维"],
        "doc_file": "02_肠道健康与饮食分类.md"
    },
    "中医养生": {
        "keywords": ["中医", "三伏", "养生", "食疗", "茶饮", "汤药", "湿气", "健脾", "温补", "穴位", "经络"],
        "doc_file": "03_中医养生与食疗.md"
    },
    "日常饮食": {
        "keywords": ["早餐", "食谱", "搭配", "热量", "蛋白质", "减脂", "饮食建议", "营养", "食物", "膳食", "宝塔"],
        "doc_file": "04_日常饮食建议.md"
    },
}


@dataclass
class ImageInfo:
    """图片信息数据类"""
    path: Path
    size: int
    size_category: str
    
    @property
    def name(self) -> str:
        return self.path.name
    
    @property
    def size_mb(self) -> float:
        return self.size / (1024 * 1024)


@dataclass
class ProcessingProgress:
    """处理进度数据类"""
    topic: str
    total_images: int
    processed_count: int
    current_batch: int
    total_batches: int
    results: List[Dict] = field(default_factory=list)
    failed_images: List[str] = field(default_factory=list)
    duplicates: List[str] = field(default_factory=list)
    start_time: str = ""
    last_update: str = ""
    status: str = "running"  # 'running', 'paused', 'completed', 'error'
    performance_stats: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessingProgress':
        return cls(**data)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    total_time: float = 0
    ocr_time: float = 0
    classification_time: float = 0
    io_time: float = 0
    images_processed: int = 0
    images_failed: int = 0
    duplicates_found: int = 0
    engine_switches: int = 0
    memory_peak_mb: float = 0
    
    @property
    def avg_time_per_image(self) -> float:
        if self.images_processed == 0:
            return 0
        return self.total_time / self.images_processed
    
    @property
    def success_rate(self) -> float:
        total = self.images_processed + self.images_failed
        if total == 0:
            return 0
        return (self.images_processed / total) * 100


class MemoryMonitor:
    """内存监控器"""
    
    def __init__(self, threshold_percent: int = MEMORY_THRESHOLD):
        self.threshold = threshold_percent
        self.peak_memory = 0
        self._stop_event = threading.Event()
        self._monitor_thread = None
    
    def start(self):
        """启动内存监控"""
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop(self):
        """停止内存监控"""
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """监控循环"""
        try:
            import psutil
            process = psutil.Process()
            
            while not self._stop_event.is_set():
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                self.peak_memory = max(self.peak_memory, memory_mb)
                
                # 获取系统内存使用率
                system_memory = psutil.virtual_memory()
                if system_memory.percent > self.threshold:
                    logger.warning(f"[WARN] 内存使用率过高: {system_memory.percent}%，触发GC")
                    gc.collect()
                
                time.sleep(2)
        except ImportError:
            logger.warning("[WARN] psutil 未安装，内存监控功能受限")
        except Exception as e:
            logger.error(f"[ERROR] 内存监控错误: {e}")
    
    def get_peak_memory(self) -> float:
        """获取峰值内存使用（MB）"""
        return self.peak_memory


class DuplicateDetector:
    """重复内容检测器"""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.processed_hashes = set()
        self.processed_texts = []
    
    def compute_hash(self, text: str) -> str:
        """计算文本哈希"""
        import hashlib
        # 简化文本后计算哈希
        simplified = ''.join(text.split())[:500]  # 取前500字符
        return hashlib.md5(simplified.encode()).hexdigest()
    
    def compute_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度（简单实现）"""
        # 使用集合计算Jaccard相似度
        set1 = set(text1[i:i+3] for i in range(len(text1)-2))
        set2 = set(text2[i:i+3] for i in range(len(text2)-2))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def is_duplicate(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        检查是否重复
        
        Returns:
            (是否重复, 匹配的原文本)
        """
        # 快速哈希检查
        text_hash = self.compute_hash(text)
        if text_hash in self.processed_hashes:
            return True, None
        
        # 相似度检查
        for existing_text in self.processed_texts:
            similarity = self.compute_similarity(text, existing_text)
            if similarity >= self.threshold:
                return True, existing_text[:100] + "..."
        
        return False, None
    
    def add_content(self, text: str):
        """添加已处理内容"""
        self.processed_hashes.add(self.compute_hash(text))
        self.processed_texts.append(text)
        
        # 限制内存使用，只保留最近100条
        if len(self.processed_texts) > 100:
            self.processed_texts = self.processed_texts[-100:]


class EnhancedOCRManager:
    """增强版OCR管理器（支持并发和自动降级）"""
    
    def __init__(self):
        self.primary_manager = OCRManager()
        self.backup_managers: Dict[OCREngine, OCRManager] = {}
        self.current_engine: Optional[OCREngine] = None
        self.engine_failures: Dict[OCREngine, int] = defaultdict(int)
        self.engine_cooldowns: Dict[OCREngine, float] = {}
        self.max_failures = 3
        self._lock = threading.Lock()
        
        # 初始化主引擎
        self._init_primary_engine()
    
    def _init_primary_engine(self):
        """初始化主引擎"""
        engine = self.primary_manager.auto_select_engine()
        if engine:
            self.current_engine = engine
            logger.info(f"[OK] 主OCR引擎初始化: {engine.value}")
        else:
            logger.error("[FAIL] 没有可用的OCR引擎")
    
    def _get_available_engine(self) -> Optional[Tuple[OCREngine, OCRManager]]:
        """获取当前可用的引擎"""
        with self._lock:
            now = time.time()
            
            # 检查当前引擎是否可用
            if self.current_engine:
                cooldown = self.engine_cooldowns.get(self.current_engine, 0)
                if now > cooldown and self.engine_failures[self.current_engine] < self.max_failures:
                    return self.current_engine, self.primary_manager
            
            # 尝试切换到备用引擎
            for engine in [OCREngine.BAIDU, OCREngine.LOCAL, OCREngine.TENCENT]:
                if engine == self.current_engine:
                    continue
                
                cooldown = self.engine_cooldowns.get(engine, 0)
                if now > cooldown and self.engine_failures[engine] < self.max_failures:
                    # 初始化备用引擎
                    if engine not in self.backup_managers:
                        manager = OCRManager()
                        if manager.init_engine(engine):
                            self.backup_managers[engine] = manager
                            logger.info(f"[OK] 备用引擎就绪: {engine.value}")
                    
                    if engine in self.backup_managers:
                        self.current_engine = engine
                        return engine, self.backup_managers[engine]
            
            return None
    
    def recognize_with_fallback(self, image_path: str, max_retries: int = 2) -> Dict:
        """
        带自动降级的识别
        
        Args:
            image_path: 图片路径
            max_retries: 最大重试次数
            
        Returns:
            识别结果
        """
        for attempt in range(max_retries + 1):
            engine_info = self._get_available_engine()
            
            if not engine_info:
                return {
                    "success": False,
                    "error": "没有可用的OCR引擎"
                }
            
            engine, manager = engine_info
            
            try:
                result = manager.recognize(image_path)
                
                if result.get("success"):
                    # 成功，重置失败计数
                    self.engine_failures[engine] = 0
                    result["engine"] = engine.value
                    return result
                
                # 检查错误类型
                error = result.get("error", "")
                if "频率" in error or "limit" in error.lower() or "quota" in error.lower():
                    logger.warning(f"[WARN] {engine.value} 频率限制，切换引擎")
                    self.engine_failures[engine] += 1
                    self.engine_cooldowns[engine] = time.time() + ENGINE_COOLDOWN * 30
                elif "超时" in error or "timeout" in error.lower():
                    logger.warning(f"[WARN] {engine.value} 超时，将重试")
                    self.engine_failures[engine] += 0.5
                else:
                    logger.error(f"[ERROR] {engine.value} 识别失败: {error}")
                    self.engine_failures[engine] += 1
                
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return result
                    
            except Exception as e:
                logger.error(f"[ERROR] {engine.value} 异常: {e}")
                self.engine_failures[engine] += 1
                
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    return {
                        "success": False,
                        "error": str(e)
                    }
        
        return {
            "success": False,
            "error": "所有重试均失败"
        }
    
    def get_current_engine_name(self) -> str:
        """获取当前引擎名称"""
        if self.current_engine:
            return self.current_engine.value
        return "未初始化"


class EnhancedBatchProcessor:
    """增强版分批处理器"""
    
    def __init__(self):
        self.ocr_manager = EnhancedOCRManager()
        self.classifier = ClassifierEngine()
        self.duplicate_detector = DuplicateDetector()
        self.memory_monitor = MemoryMonitor()
        self.metrics = PerformanceMetrics()
        
        self.progress_dir = PROGRESS_DIR
        self.is_paused = False
        self.current_progress: Optional[ProcessingProgress] = None
        
        # 结果缓存（用于增量写入）
        self.result_buffer: Dict[str, List[Dict]] = defaultdict(list)
        self.buffer_size = 5  # 每5个结果写入一次
    
    def analyze_images(self, images: List[Path]) -> List[ImageInfo]:
        """
        分析图片列表，按大小分类
        
        Args:
            images: 图片路径列表
            
        Returns:
            图片信息列表
        """
        image_infos = []
        
        for img_path in images:
            size = img_path.stat().st_size
            
            # 确定大小分类
            if size < BATCH_CONFIG["small"]["max_size"]:
                category = "small"
            elif size < BATCH_CONFIG["medium"]["max_size"]:
                category = "medium"
            elif size < BATCH_CONFIG["large"]["max_size"]:
                category = "large"
            else:
                category = "xlarge"
            
            image_infos.append(ImageInfo(path=img_path, size=size, size_category=category))
        
        return image_infos
    
    def create_smart_batches(self, image_infos: List[ImageInfo]) -> List[List[ImageInfo]]:
        """
        创建智能批次
        
        策略：
        1. 按大小分类分组
        2. 同类图片组成批次
        3. 控制每批总大小（避免内存溢出）
        
        Args:
            image_infos: 图片信息列表
            
        Returns:
            批次列表
        """
        # 按大小分类分组
        by_category = defaultdict(list)
        for info in image_infos:
            by_category[info.size_category].append(info)
        
        batches = []
        
        # 处理顺序：小图 → 中图 → 大图 → 超大图
        for category in ["small", "medium", "large", "xlarge"]:
            images = by_category.get(category, [])
            if not images:
                continue
            
            batch_size = BATCH_CONFIG[category]["batch_size"]
            
            # 创建批次
            for i in range(0, len(images), batch_size):
                batch = images[i:i + batch_size]
                batches.append(batch)
        
        return batches
    
    def process_single_image(self, image_info: ImageInfo) -> Dict:
        """
        处理单张图片
        
        Args:
            image_info: 图片信息
            
        Returns:
            处理结果
        """
        start_time = time.time()
        
        try:
            # OCR识别
            ocr_start = time.time()
            ocr_result = self.ocr_manager.recognize_with_fallback(str(image_info.path))
            ocr_time = time.time() - ocr_start
            
            if not ocr_result.get("success"):
                return {
                    "image_name": image_info.name,
                    "image_path": str(image_info.path),
                    "success": False,
                    "error": ocr_result.get("error", "OCR失败"),
                    "ocr_time": ocr_time
                }
            
            text = ocr_result.get("text", "")
            
            # 重复检测
            is_dup, dup_text = self.duplicate_detector.is_duplicate(text)
            if is_dup:
                return {
                    "image_name": image_info.name,
                    "image_path": str(image_info.path),
                    "success": True,
                    "is_duplicate": True,
                    "text": text[:200] + "..." if len(text) > 200 else text,
                    "ocr_time": ocr_time,
                    "total_time": time.time() - start_time
                }
            
            # 分类
            classify_start = time.time()
            category_result = self.classifier.classify(text)
            classify_time = time.time() - classify_start
            
            # 添加到重复检测器
            self.duplicate_detector.add_content(text)
            
            total_time = time.time() - start_time
            
            return {
                "image_name": image_info.name,
                "image_path": str(image_info.path),
                "success": True,
                "text": text,
                "category": category_result.category,
                "confidence": category_result.confidence,
                "engine": ocr_result.get("engine", "未知"),
                "is_duplicate": False,
                "ocr_time": ocr_time,
                "classify_time": classify_time,
                "total_time": total_time
            }
            
        except Exception as e:
            return {
                "image_name": image_info.name,
                "image_path": str(image_info.path),
                "success": False,
                "error": str(e),
                "total_time": time.time() - start_time
            }
    
    def process_batch_concurrent(self, batch: List[ImageInfo], batch_num: int, 
                                  total_batches: int) -> List[Dict]:
        """
        并发处理批次
        
        Args:
            batch: 批次图片列表
            batch_num: 批次编号
            total_batches: 总批次数
            
        Returns:
            处理结果列表
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"处理批次 {batch_num}/{total_batches} ({len(batch)} 张图片)")
        logger.info(f"图片大小: {[f'{img.size_mb:.2f}MB' for img in batch]}")
        logger.info(f"{'='*60}")
        
        results = []
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(batch))) as executor:
            # 提交所有任务
            future_to_image = {
                executor.submit(self.process_single_image, img_info): img_info 
                for img_info in batch
            }
            
            # 收集结果
            for future in as_completed(future_to_image):
                img_info = future_to_image[future]
                try:
                    result = future.result(timeout=60)  # 单张超时60秒
                    results.append(result)
                    
                    if result.get("success"):
                        if result.get("is_duplicate"):
                            logger.info(f"[DUP] {img_info.name} - 重复内容，跳过")
                            self.metrics.duplicates_found += 1
                        else:
                            logger.info(f"[OK] {img_info.name} -> {result.get('category', '未知')} "
                                      f"(OCR:{result.get('ocr_time', 0):.1f}s)")
                            self.metrics.images_processed += 1
                    else:
                        logger.error(f"[FAIL] {img_info.name}: {result.get('error', '未知错误')}")
                        self.metrics.images_failed += 1
                        
                except Exception as e:
                    logger.error(f"[FAIL] {img_info.name}: 处理异常 - {e}")
                    results.append({
                        "image_name": img_info.name,
                        "image_path": str(img_info.path),
                        "success": False,
                        "error": str(e)
                    })
                    self.metrics.images_failed += 1
        
        return results
    
    def save_batch_results(self, results: List[Dict], topic: str, batch_num: int):
        """
        保存批次结果（增量写入）
        
        Args:
            results: 批次处理结果
            topic: 主题名称
            batch_num: 批次编号
        """
        # 按分类分组
        categorized = defaultdict(list)
        for result in results:
            if not result.get("success") or result.get("is_duplicate"):
                continue
            category = result.get("category", "新主题")
            categorized[category].append(result)
        
        # 保存到各分类文档
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
            content = f"\n## 批次{batch_num} - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            
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
            else:
                header = f"# {doc_title}\n\n"
                header += f"> 整理来源：图片识别自动归档\n"
                header += f"> 创建时间：{datetime.now().strftime('%Y-%m-%d')}\n\n"
                with open(doc_file, 'w', encoding='utf-8') as f:
                    f.write(header + content)
            
            logger.info(f"[OK] 批次{batch_num} 已追加到: {doc_file.name} ({len(items)} 条)")
    
    def archive_batch_images(self, results: List[Dict], topic: str, batch_num: int):
        """归档批次图片"""
        archive_dir = PROCESSED_DIR / topic / f"batch_{batch_num:03d}_{datetime.now().strftime('%Y%m%d')}"
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        archived_count = 0
        for result in results:
            if result.get("success"):
                src_path = Path(result["image_path"])
                dst_path = archive_dir / src_path.name
                
                try:
                    if src_path.exists():
                        shutil.move(str(src_path), str(dst_path))
                        archived_count += 1
                except Exception as e:
                    logger.error(f"归档失败 {src_path.name}: {e}")
        
        logger.info(f"[OK] 批次{batch_num} 已归档 {archived_count} 张图片")
    
    def save_progress(self, progress: ProcessingProgress):
        """保存处理进度"""
        progress_file = self.progress_dir / f"{progress.topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        progress.last_update = datetime.now().isoformat()
        progress.performance_stats = {
            "total_time": self.metrics.total_time,
            "images_processed": self.metrics.images_processed,
            "images_failed": self.metrics.images_failed,
            "duplicates_found": self.metrics.duplicates_found,
            "engine_switches": self.metrics.engine_switches,
            "memory_peak_mb": self.memory_monitor.get_peak_memory()
        }
        
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress.to_dict(), f, ensure_ascii=False, indent=2)
        
        return progress_file
    
    def process_topic(self, topic: str, images: List[Path]) -> ProcessingProgress:
        """
        处理一个主题的所有图片
        
        Args:
            topic: 主题名称
            images: 图片路径列表
            
        Returns:
            处理进度
        """
        start_time = time.time()
        
        # 启动内存监控
        self.memory_monitor.start()
        
        # 分析图片
        logger.info(f"\n{'='*60}")
        logger.info(f"开始分析主题: {topic}")
        logger.info(f"{'='*60}")
        
        image_infos = self.analyze_images(images)
        
        # 统计
        size_stats = defaultdict(int)
        for info in image_infos:
            size_stats[info.size_category] += 1
        
        logger.info(f"图片分析完成:")
        for cat, count in size_stats.items():
            logger.info(f"  {cat}: {count} 张 (批次大小: {BATCH_CONFIG[cat]['batch_size']})")
        
        # 创建智能批次
        batches = self.create_smart_batches(image_infos)
        total_batches = len(batches)
        total_images = len(images)
        
        logger.info(f"\n总图片数: {total_images}")
        logger.info(f"总批次数: {total_batches}")
        logger.info(f"当前引擎: {self.ocr_manager.get_current_engine_name()}")
        
        # 初始化进度
        progress = ProcessingProgress(
            topic=topic,
            total_images=total_images,
            processed_count=0,
            current_batch=0,
            total_batches=total_batches,
            start_time=datetime.now().isoformat(),
            last_update=datetime.now().isoformat(),
            status='running'
        )
        self.current_progress = progress
        
        # 处理批次
        for batch_num, batch in enumerate(batches, 1):
            if self.is_paused:
                progress.status = 'paused'
                self.save_progress(progress)
                logger.info("[PAUSE] 处理已暂停")
                return progress
            
            batch_start = time.time()
            
            # 处理批次
            batch_results = self.process_batch_concurrent(batch, batch_num, total_batches)
            
            # 更新进度
            progress.current_batch = batch_num
            progress.processed_count += len(batch)
            progress.results.extend(batch_results)
            
            # 收集失败和重复
            for result in batch_results:
                if not result.get("success"):
                    progress.failed_images.append(result["image_name"])
                elif result.get("is_duplicate"):
                    progress.duplicates.append(result["image_name"])
            
            # 保存结果
            self.save_batch_results(batch_results, topic, batch_num)
            self.archive_batch_images(batch_results, topic, batch_num)
            
            # 保存进度
            self.save_progress(progress)
            
            # 显示进度
            batch_time = time.time() - batch_start
            progress_pct = (progress.processed_count / total_images) * 100
            
            logger.info(f"\n[PROGRESS] 批次 {batch_num}/{total_batches} 完成")
            logger.info(f"[PROGRESS] 总进度: {progress.processed_count}/{total_images} ({progress_pct:.1f}%)")
            logger.info(f"[PROGRESS] 批次耗时: {batch_time:.1f}s")
            logger.info(f"[PROGRESS] 成功: {self.metrics.images_processed}")
            logger.info(f"[PROGRESS] 失败: {self.metrics.images_failed}")
            logger.info(f"[PROGRESS] 重复: {self.metrics.duplicates_found}")
            logger.info(f"[PROGRESS] 内存峰值: {self.memory_monitor.get_peak_memory():.1f}MB")
            
            # 批次间休息
            if batch_num < total_batches:
                time.sleep(BATCH_INTERVAL)
                gc.collect()  # 主动GC
        
        # 处理完成
        self.metrics.total_time = time.time() - start_time
        progress.status = 'completed'
        self.save_progress(progress)
        
        # 停止内存监控
        self.memory_monitor.stop()
        self.metrics.memory_peak_mb = self.memory_monitor.get_peak_memory()
        
        # 输出最终报告
        self._print_final_report(topic)
        
        return progress
    
    def _print_final_report(self, topic: str):
        """打印最终报告"""
        logger.info(f"\n{'='*60}")
        logger.info(f"主题「{topic}」处理完成!")
        logger.info(f"{'='*60}")
        logger.info(f"总计处理: {self.current_progress.total_images} 张")
        logger.info(f"成功识别: {self.metrics.images_processed} 张")
        logger.info(f"识别失败: {self.metrics.images_failed} 张")
        logger.info(f"重复内容: {self.metrics.duplicates_found} 张")
        logger.info(f"成功率: {self.metrics.success_rate:.1f}%")
        logger.info(f"总耗时: {self.metrics.total_time:.1f} 秒")
        logger.info(f"平均每张: {self.metrics.avg_time_per_image:.1f} 秒")
        logger.info(f"内存峰值: {self.metrics.memory_peak_mb:.1f} MB")
        logger.info(f"引擎切换: {self.metrics.engine_switches} 次")
        logger.info(f"{'='*60}\n")
    
    def pause(self):
        """暂停处理"""
        self.is_paused = True
        logger.info("[PAUSE] 正在暂停...")
    
    def resume(self, progress_file: Path):
        """恢复处理"""
        # 简化实现，实际应加载进度并继续
        logger.info("[RESUME] 恢复处理功能待完善")


def main():
    """测试增强版分批处理器"""
    print("=" * 60)
    print("增强版分批图片处理器 v2.0")
    print("=" * 60)
    
    processor = EnhancedBatchProcessor()
    
    # 扫描待处理图片
    pending_images = {}
    if PENDING_DIR.exists():
        for topic_dir in PENDING_DIR.iterdir():
            if not topic_dir.is_dir():
                continue
            images = [f for f in topic_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS]
            if images:
                pending_images[topic_dir.name] = sorted(images)
    
    if not pending_images:
        logger.info("没有待处理的图片")
        return
    
    logger.info(f"发现 {len(pending_images)} 个主题待处理")
    
    # 处理每个主题
    for topic, images in pending_images.items():
        processor.process_topic(topic, images)
    
    logger.info("\n[OK] 所有图片处理完成!")


if __name__ == "__main__":
    main()
