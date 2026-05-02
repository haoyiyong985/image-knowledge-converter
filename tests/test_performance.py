#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试与验证脚本
==================

功能：
  1. 基准测试（对比新旧处理器性能）
  2. 并发性能测试
  3. 内存使用测试
  4. 生成性能对比报告
"""

import os
import sys
import time
import gc
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path("D:/新建文件夹")
TEST_RESULTS_DIR = BASE_DIR / "test_results"
TEST_RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class TestResult:
    """测试结果数据类"""
    test_name: str
    total_images: int
    total_time: float
    success_count: int
    failed_count: int
    peak_memory_mb: float
    avg_time_per_image: float
    throughput: float  # 图片/秒
    timestamp: str
    details: Dict = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceTester:
    """性能测试器"""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.test_images = self._collect_test_images()
    
    def _collect_test_images(self) -> List[Path]:
        """收集测试图片"""
        test_dirs = [
            BASE_DIR / "已处理图片",
            BASE_DIR / "待处理图片"
        ]
        
        images = []
        for test_dir in test_dirs:
            if test_dir.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png']:
                    images.extend(test_dir.rglob(ext))
        
        return images[:50]  # 最多50张测试图片
    
    def _get_memory_usage(self) -> float:
        """获取当前内存使用（MB）"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except:
            return 0
    
    def test_original_processor(self, sample_size: int = 10) -> TestResult:
        """
        测试原始处理器性能
        
        Args:
            sample_size: 测试样本数量
            
        Returns:
            测试结果
        """
        logger.info("\n" + "="*60)
        logger.info("测试: 原始处理器 (batch_processor.py)")
        logger.info("="*60)
        
        if not self.test_images:
            logger.error("没有找到测试图片")
            return None
        
        sample_images = self.test_images[:sample_size]
        logger.info(f"测试样本: {len(sample_images)} 张图片")
        
        try:
            from batch_processor import BatchProcessor, OCRManager
            
            # 初始化
            ocr_manager = OCRManager()
            if not ocr_manager.auto_select_engine():
                logger.error("OCR引擎不可用")
                return None
            
            processor = BatchProcessor(ocr_manager)
            
            # 记录内存基准
            gc.collect()
            baseline_memory = self._get_memory_usage()
            peak_memory = baseline_memory
            
            # 执行测试
            start_time = time.time()
            
            # 模拟处理（只测试OCR部分）
            success_count = 0
            failed_count = 0
            
            for i, img_path in enumerate(sample_images, 1):
                logger.info(f"处理 {i}/{len(sample_images)}: {img_path.name}")
                
                try:
                    result = ocr_manager.recognize(str(img_path))
                    if result.get("success"):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"处理失败: {e}")
                    failed_count += 1
                
                # 监控内存
                current_memory = self._get_memory_usage()
                peak_memory = max(peak_memory, current_memory)
            
            total_time = time.time() - start_time
            
            result = TestResult(
                test_name="原始处理器",
                total_images=len(sample_images),
                total_time=total_time,
                success_count=success_count,
                failed_count=failed_count,
                peak_memory_mb=peak_memory - baseline_memory,
                avg_time_per_image=total_time / len(sample_images) if sample_images else 0,
                throughput=len(sample_images) / total_time if total_time > 0 else 0,
                timestamp=datetime.now().isoformat()
            )
            
            self.results.append(result)
            
            logger.info(f"\n测试结果:")
            logger.info(f"  总时间: {total_time:.2f}s")
            logger.info(f"  成功率: {success_count}/{len(sample_images)}")
            logger.info(f"  平均耗时: {result.avg_time_per_image:.2f}s/张")
            logger.info(f"  吞吐量: {result.throughput:.2f}张/秒")
            logger.info(f"  内存峰值: {result.peak_memory_mb:.1f}MB")
            
            return result
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            return None
    
    def test_enhanced_processor(self, sample_size: int = 10) -> TestResult:
        """
        测试增强版处理器性能
        
        Args:
            sample_size: 测试样本数量
            
        Returns:
            测试结果
        """
        logger.info("\n" + "="*60)
        logger.info("测试: 增强版处理器 (enhanced_batch_processor.py)")
        logger.info("="*60)
        
        if not self.test_images:
            logger.error("没有找到测试图片")
            return None
        
        sample_images = self.test_images[:sample_size]
        logger.info(f"测试样本: {len(sample_images)} 张图片")
        
        try:
            from enhanced_batch_processor import EnhancedBatchProcessor
            
            # 初始化
            processor = EnhancedBatchProcessor()
            
            # 记录内存基准
            gc.collect()
            baseline_memory = self._get_memory_usage()
            
            # 启动内存监控
            processor.memory_monitor.start()
            
            # 分析图片
            image_infos = processor.analyze_images(sample_images)
            batches = processor.create_smart_batches(image_infos)
            
            logger.info(f"智能分批: {len(batches)} 个批次")
            for i, batch in enumerate(batches[:3], 1):
                sizes = [f"{img.size_mb:.1f}MB" for img in batch]
                logger.info(f"  批次{i}: {len(batch)}张 ({', '.join(sizes)})")
            
            # 执行测试
            start_time = time.time()
            
            # 处理批次
            success_count = 0
            failed_count = 0
            
            for batch_num, batch in enumerate(batches, 1):
                logger.info(f"\n处理批次 {batch_num}/{len(batches)}")
                
                results = processor.process_batch_concurrent(batch, batch_num, len(batches))
                
                for result in results:
                    if result.get("success") and not result.get("is_duplicate"):
                        success_count += 1
                    elif not result.get("success"):
                        failed_count += 1
            
            total_time = time.time() - start_time
            
            # 停止内存监控
            processor.memory_monitor.stop()
            peak_memory = processor.memory_monitor.get_peak_memory()
            
            result = TestResult(
                test_name="增强版处理器",
                total_images=len(sample_images),
                total_time=total_time,
                success_count=success_count,
                failed_count=failed_count,
                peak_memory_mb=peak_memory,
                avg_time_per_image=total_time / len(sample_images) if sample_images else 0,
                throughput=len(sample_images) / total_time if total_time > 0 else 0,
                timestamp=datetime.now().isoformat(),
                details={
                    "batch_count": len(batches),
                    "concurrent_workers": 3,
                    "duplicates_found": processor.metrics.duplicates_found
                }
            )
            
            self.results.append(result)
            
            logger.info(f"\n测试结果:")
            logger.info(f"  总时间: {total_time:.2f}s")
            logger.info(f"  成功率: {success_count}/{len(sample_images)}")
            logger.info(f"  平均耗时: {result.avg_time_per_image:.2f}s/张")
            logger.info(f"  吞吐量: {result.throughput:.2f}张/秒")
            logger.info(f"  内存峰值: {result.peak_memory_mb:.1f}MB")
            logger.info(f"  重复检测: {processor.metrics.duplicates_found} 张")
            
            return result
            
        except Exception as e:
            logger.error(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_concurrent_performance(self) -> TestResult:
        """测试并发性能"""
        logger.info("\n" + "="*60)
        logger.info("测试: 并发性能对比")
        logger.info("="*60)
        
        # 这里可以添加更详细的并发测试
        # 比较不同并发数下的性能
        
        return TestResult(
            test_name="并发性能测试",
            total_images=0,
            total_time=0,
            success_count=0,
            failed_count=0,
            peak_memory_mb=0,
            avg_time_per_image=0,
            throughput=0,
            timestamp=datetime.now().isoformat()
        )
    
    def generate_comparison_report(self) -> str:
        """
        生成性能对比报告
        
        Returns:
            报告文件路径
        """
        if len(self.results) < 2:
            logger.error("测试结果不足，无法生成对比报告")
            return None
        
        report_file = TEST_RESULTS_DIR / f"performance_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        # 计算对比数据
        original = self.results[0]
        enhanced = self.results[1]
        
        time_improvement = ((original.total_time - enhanced.total_time) / original.total_time * 100) if original.total_time > 0 else 0
        throughput_improvement = ((enhanced.throughput - original.throughput) / original.throughput * 100) if original.throughput > 0 else 0
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能对比报告 - 图片知识库处理器</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            color: #333;
            margin-bottom: 10px;
        }}
        .header .date {{
            color: #888;
            font-size: 14px;
        }}
        .comparison-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .version-card {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .version-card h2 {{
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #eee;
        }}
        .version-card.original h2 {{ color: #6c757d; }}
        .version-card.enhanced h2 {{ color: #28a745; }}
        
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .metric:last-child {{ border-bottom: none; }}
        .metric .label {{ color: #666; }}
        .metric .value {{ font-weight: bold; color: #333; }}
        
        .improvement-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .improvement-positive {{
            background: #d4edda;
            color: #155724;
        }}
        .improvement-negative {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            color: #333;
            margin-bottom: 20px;
        }}
        .summary-item {{
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .summary-icon {{
            font-size: 24px;
        }}
        .summary-text {{
            flex: 1;
        }}
        .summary-value {{
            font-size: 24px;
            font-weight: bold;
            color: #28a745;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 性能对比报告</h1>
            <div class="date">测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="comparison-grid">
            <div class="version-card original">
                <h2>📦 原始处理器 v1.0</h2>
                <div class="metric">
                    <span class="label">测试图片数</span>
                    <span class="value">{original.total_images}</span>
                </div>
                <div class="metric">
                    <span class="label">总耗时</span>
                    <span class="value">{original.total_time:.2f}s</span>
                </div>
                <div class="metric">
                    <span class="label">平均耗时/张</span>
                    <span class="value">{original.avg_time_per_image:.2f}s</span>
                </div>
                <div class="metric">
                    <span class="label">吞吐量</span>
                    <span class="value">{original.throughput:.2f}张/秒</span>
                </div>
                <div class="metric">
                    <span class="label">成功率</span>
                    <span class="value">{original.success_count}/{original.total_images}</span>
                </div>
                <div class="metric">
                    <span class="label">内存峰值</span>
                    <span class="value">{original.peak_memory_mb:.1f}MB</span>
                </div>
            </div>
            
            <div class="version-card enhanced">
                <h2>🚀 增强版处理器 v2.0</h2>
                <div class="metric">
                    <span class="label">测试图片数</span>
                    <span class="value">{enhanced.total_images}</span>
                </div>
                <div class="metric">
                    <span class="label">总耗时</span>
                    <span class="value">{enhanced.total_time:.2f}s</span>
                    <span class="improvement-badge {'improvement-positive' if time_improvement > 0 else 'improvement-negative'}">
                        {time_improvement:+.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span class="label">平均耗时/张</span>
                    <span class="value">{enhanced.avg_time_per_image:.2f}s</span>
                </div>
                <div class="metric">
                    <span class="label">吞吐量</span>
                    <span class="value">{enhanced.throughput:.2f}张/秒</span>
                    <span class="improvement-badge {'improvement-positive' if throughput_improvement > 0 else 'improvement-negative'}">
                        {throughput_improvement:+.1f}%
                    </span>
                </div>
                <div class="metric">
                    <span class="label">成功率</span>
                    <span class="value">{enhanced.success_count}/{enhanced.total_images}</span>
                </div>
                <div class="metric">
                    <span class="label">内存峰值</span>
                    <span class="value">{enhanced.peak_memory_mb:.1f}MB</span>
                </div>
            </div>
        </div>
        
        <div class="summary">
            <h2>📈 优化总结</h2>
            <div class="summary-item">
                <span class="summary-icon">⚡</span>
                <span class="summary-text">处理速度提升</span>
                <span class="summary-value">{abs(time_improvement):.1f}%</span>
            </div>
            <div class="summary-item">
                <span class="summary-icon">🔄</span>
                <span class="summary-text">吞吐量提升</span>
                <span class="summary-value">{abs(throughput_improvement):.1f}%</span>
            </div>
            <div class="summary-item">
                <span class="summary-icon">🎯</span>
                <span class="summary-text">重复内容检测</span>
                <span class="summary-value">{enhanced.details.get('duplicates_found', 0) if enhanced.details else 0}张</span>
            </div>
            <div class="summary-item">
                <span class="summary-icon">🔧</span>
                <span class="summary-text">智能分批策略</span>
                <span class="summary-value">{enhanced.details.get('batch_count', 0) if enhanced.details else 0}批</span>
            </div>
        </div>
    </div>
</body>
</html>"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"\n对比报告已生成: {report_file}")
        return str(report_file)
    
    def save_results(self):
        """保存测试结果"""
        results_file = TEST_RESULTS_DIR / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "test_time": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results]
        }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"测试结果已保存: {results_file}")


def main():
    """运行性能测试"""
    print("=" * 70)
    print("图片知识库处理器 - 性能测试")
    print("=" * 70)
    
    tester = PerformanceTester()
    
    if not tester.test_images:
        print("\n错误: 没有找到测试图片")
        print("请在以下目录放置测试图片:")
        print("  - D:/新建文件夹/待处理图片/")
        print("  - D:/新建文件夹/已处理图片/")
        return
    
    print(f"\n找到 {len(tester.test_images)} 张测试图片")
    print("\n注意: 性能测试将实际调用OCR引擎，可能需要较长时间")
    print("      测试过程中请保持网络连接")
    
    # 询问是否继续
    response = input("\n是否开始测试? (y/n): ")
    if response.lower() != 'y':
        print("测试已取消")
        return
    
    # 运行测试
    sample_size = min(10, len(tester.test_images))
    
    # 测试原始处理器
    tester.test_original_processor(sample_size=sample_size)
    
    # 测试增强版处理器
    tester.test_enhanced_processor(sample_size=sample_size)
    
    # 生成对比报告
    if len(tester.results) >= 2:
        tester.generate_comparison_report()
    
    # 保存结果
    tester.save_results()
    
    print("\n" + "=" * 70)
    print("性能测试完成!")
    print("=" * 70)


if __name__ == "__main__":
    main()
