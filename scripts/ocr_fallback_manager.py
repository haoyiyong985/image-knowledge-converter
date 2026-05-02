#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 三层回退管理器
自动检测可用引擎，按优先级回退

优先级：腾讯云 OCR → 百度 OCR → 本地 Tesseract

使用方式：
    from ocr_fallback_manager import OCRManager
    
    ocr = OCRManager()
    result = ocr.recognize("image.jpg")
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class OCREngine(Enum):
    """OCR 引擎枚举"""
    TENCENT = "tencent"      # 腾讯云 OCR
    BAIDU = "baidu"          # 百度 OCR
    TESSERACT = "tesseract"  # 本地 Tesseract
    NONE = "none"            # 无可用引擎


class OCRStatus:
    """OCR 引擎状态"""
    
    def __init__(self):
        self.tencent: Dict = {"available": False, "reason": ""}
        self.baidu: Dict = {"available": False, "reason": ""}
        self.tesseract: Dict = {"available": False, "reason": ""}
    
    def get_available_engines(self) -> List[OCREngine]:
        """获取可用的引擎列表，按优先级排序"""
        engines = []
        if self.tencent["available"]:
            engines.append(OCREngine.TENCENT)
        if self.baidu["available"]:
            engines.append(OCREngine.BAIDU)
        if self.tesseract["available"]:
            engines.append(OCREngine.TESSERACT)
        return engines
    
    def __str__(self) -> str:
        lines = ["OCR 引擎状态:"]
        lines.append(f"  腾讯云 OCR: {'[OK]' if self.tencent['available'] else '[FAIL] ' + self.tencent['reason']}")
        lines.append(f"  百度 OCR:   {'[OK]' if self.baidu['available'] else '[FAIL] ' + self.baidu['reason']}")
        lines.append(f"  Tesseract: {'[OK]' if self.tesseract['available'] else '[FAIL] ' + self.tesseract['reason']}")
        return "\n".join(lines)


class OCRManager:
    """
    OCR 三层回退管理器
    
    自动检测可用的 OCR 引擎，按优先级调用
    当某一引擎失败时，自动回退到下一级引擎
    """
    
    # 引擎优先级（数字越小优先级越高）
    ENGINE_PRIORITY = {
        OCREngine.TENCENT: 1,
        OCREngine.BAIDU: 2,
        OCREngine.TESSERACT: 3
    }
    
    def __init__(self, config: Dict = None):
        """
        初始化 OCR 管理器
        
        Args:
            config: 可选配置字典，包含各引擎的密钥等
        """
        self.config = config or {}
        self.status = OCRStatus()
        self._engines: Dict[OCREngine, any] = {}
        
        # 自动检测可用引擎
        self._detect_engines()
    
    def _detect_engines(self):
        """检测可用的 OCR 引擎"""
        logger.info("=" * 50)
        logger.info("检测可用 OCR 引擎...")
        logger.info("=" * 50)
        
        # 1. 检测腾讯云 OCR
        self._detect_tencent()
        
        # 2. 检测百度 OCR
        self._detect_baidu()
        
        # 3. 检测本地 Tesseract（最重要：完全免费）
        self._detect_tesseract()
        
        # 输出状态
        logger.info(f"\n{self.status}")
        
        available = self.status.get_available_engines()
        if available:
            primary = available[0]
            logger.info(f"将使用 {primary.value.upper()} 作为主引擎")
        else:
            logger.warning("⚠️ 没有任何可用的 OCR 引擎！")
    
    def _detect_tencent(self):
        """检测腾讯云 OCR"""
        try:
            secret_id = self.config.get('secret_id') or os.getenv('TENCENT_SECRET_ID')
            secret_key = self.config.get('secret_key') or os.getenv('TENCENT_SECRET_KEY')
            
            if not secret_id or not secret_key:
                self.status.tencent = {"available": False, "reason": "未配置密钥"}
                return
            
            # 尝试初始化
            from tencent_ocr import TencentOCR
            ocr = TencentOCR(secret_id, secret_key)
            self._engines[OCREngine.TENCENT] = ocr
            self.status.tencent = {"available": True, "reason": "已配置"}
            logger.info("✓ 腾讯云 OCR 可用")
            
        except ImportError:
            self.status.tencent = {"available": False, "reason": "未安装SDK"}
        except ValueError as e:
            self.status.tencent = {"available": False, "reason": str(e)}
        except Exception as e:
            self.status.tencent = {"available": False, "reason": f"初始化失败: {e}"}
    
    def _detect_baidu(self):
        """检测百度 OCR"""
        try:
            app_id = self.config.get('app_id') or os.getenv('BAIDU_APP_ID')
            api_key = self.config.get('api_key') or os.getenv('BAIDU_API_KEY')
            secret_key = self.config.get('secret_key') or os.getenv('BAIDU_SECRET_KEY')
            
            if not all([app_id, api_key, secret_key]):
                self.status.baidu = {"available": False, "reason": "未配置密钥"}
                return
            
            # 尝试初始化
            from baidu_ocr import BaiduOCR
            ocr = BaiduOCR(app_id, api_key, secret_key)
            self._engines[OCREngine.BAIDU] = ocr
            self.status.baidu = {"available": True, "reason": "已配置"}
            logger.info("✓ 百度 OCR 可用")
            
        except ImportError:
            self.status.baidu = {"available": False, "reason": "未安装SDK"}
        except ValueError as e:
            self.status.baidu = {"available": False, "reason": str(e)}
        except Exception as e:
            self.status.baidu = {"available": False, "reason": f"初始化失败: {e}"}
    
    def _detect_tesseract(self):
        """检测本地 Tesseract OCR（关键：完全免费）"""
        try:
            from local_ocr import LocalOCR
            
            # 尝试初始化
            ocr = LocalOCR()
            if ocr.tesseract_available:
                self._engines[OCREngine.TESSERACT] = ocr
                self.status.tesseract = {"available": True, "reason": "已安装"}
                logger.info("✓ 本地 Tesseract OCR 可用（完全免费）")
            else:
                self.status.tesseract = {"available": False, "reason": "Tesseract 未正确安装"}
                
        except ImportError:
            self.status.tesseract = {"available": False, "reason": "未安装 pytesseract"}
        except Exception as e:
            self.status.tesseract = {"available": False, "reason": f"未安装或配置错误: {e}"}
    
    def get_primary_engine(self) -> Optional[OCREngine]:
        """获取主引擎"""
        available = self.status.get_available_engines()
        return available[0] if available else None
    
    def get_engine_name(self, engine: OCREngine) -> str:
        """获取引擎显示名称"""
        names = {
            OCREngine.TENCENT: "腾讯云 OCR",
            OCREngine.BAIDU: "百度 OCR",
            OCREngine.TESSERACT: "本地 Tesseract",
            OCREngine.NONE: "无"
        }
        return names.get(engine, str(engine))
    
    def recognize(self, image_path: str, preferred_engine: OCREngine = None) -> Dict:
        """
        识别单张图片（带三层回退）
        
        Args:
            image_path: 图片路径
            preferred_engine: 优先使用的引擎（可选）
            
        Returns:
            识别结果字典
        """
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": f"图片不存在: {image_path}"
            }
        
        # 确定尝试顺序
        available = self.status.get_available_engines()
        if not available:
            return {
                "success": False,
                "error": "没有可用的 OCR 引擎"
            }
        
        # 如果指定了优先引擎，调整顺序
        if preferred_engine and preferred_engine in available:
            engines_to_try = [preferred_engine] + [e for e in available if e != preferred_engine]
        else:
            engines_to_try = available
        
        last_error = None
        engine_tried = []
        
        for engine in engines_to_try:
            if engine not in self._engines:
                continue
                
            try:
                ocr = self._engines[engine]
                engine_name = self.get_engine_name(engine)
                logger.info(f"尝试使用 {engine_name} 识别...")
                
                result = ocr.recognize(image_path)
                
                if result.get("success"):
                    result["engine_used"] = engine.value
                    result["engine_name"] = engine_name
                    logger.info(f"✓ {engine_name} 识别成功!")
                    return result
                else:
                    last_error = result.get("error", "未知错误")
                    engine_tried.append(engine_name)
                    logger.warning(f"✗ {engine_name} 识别失败: {last_error}")
                    
            except Exception as e:
                last_error = str(e)
                engine_tried.append(engine_name)
                logger.warning(f"✗ {engine_name} 调用异常: {e}")
        
        # 所有引擎都失败
        return {
            "success": False,
            "error": f"所有 OCR 引擎都失败了 (尝试过: {', '.join(engine_tried)})",
            "last_error": last_error
        }
    
    def recognize_batch(self, image_paths: List[str], 
                       preferred_engine: OCREngine = None,
                       on_engine_fallback: callable = None) -> List[Dict]:
        """
        批量识别图片（带回退）
        
        Args:
            image_paths: 图片路径列表
            preferred_engine: 优先使用的引擎
            on_engine_fallback: 引擎回退时的回调函数 (engine_name, image_path) -> None
            
        Returns:
            识别结果列表
        """
        results = []
        total = len(image_paths)
        
        # 获取可用引擎
        available = self.status.get_available_engines()
        if not available:
            logger.error("没有可用的 OCR 引擎")
            return [{"success": False, "error": "没有可用的 OCR 引擎"} for _ in image_paths]
        
        # 确定主引擎
        if preferred_engine and preferred_engine in available:
            current_engine = preferred_engine
        else:
            current_engine = available[0]
        
        logger.info(f"开始批量识别 {total} 张图片...")
        logger.info(f"主引擎: {self.get_engine_name(current_engine)}")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"[{i}/{total}] 处理: {Path(image_path).name}")
            
            result = self.recognize(image_path, preferred_engine=current_engine)
            results.append(result)
            
            # 如果主引擎失败，尝试切换到其他引擎
            if not result.get("success") and len(available) > 1:
                # 尝试备用引擎
                for backup_engine in available:
                    if backup_engine == current_engine:
                        continue
                    
                    logger.info(f"尝试备用引擎: {self.get_engine_name(backup_engine)}")
                    
                    if on_engine_fallback:
                        on_engine_fallback(self.get_engine_name(backup_engine), image_path)
                    
                    backup_result = self.recognize(image_path, preferred_engine=backup_engine)
                    
                    if backup_result.get("success"):
                        results[-1] = backup_result
                        current_engine = backup_engine
                        break
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        engine_used = {}
        for r in results:
            if r.get("success"):
                engine = r.get("engine_used", "unknown")
                engine_used[engine] = engine_used.get(engine, 0) + 1
        
        logger.info(f"\n批量识别完成: {success_count}/{total} 成功")
        logger.info(f"引擎使用统计: {engine_used}")
        
        return results
    
    def is_tesseract_installed(self) -> bool:
        """检查 Tesseract 是否已安装"""
        return self.status.tesseract["available"]
    
    def is_cloud_available(self) -> bool:
        """检查是否有云端 OCR 可用"""
        return self.status.tencent["available"] or self.status.baidu["available"]


def check_tesseract_installation() -> Dict:
    """
    独立函数：检查 Tesseract 安装状态
    
    Returns:
        安装状态字典
    """
    return {
        "pytesseract_installed": False,
        "tesseract_installed": False,
        "tesseract_path": None,
        "tesseract_version": None,
        "chinese_support": False,
        "message": ""
    }


def auto_install_tesseract():
    """
    自动安装 Tesseract 指引
    
    在 Windows 上尝试打开下载页面
    """
    import platform
    import webbrowser
    
    logger.info("正在打开 Tesseract 下载页面...")
    
    if platform.system() == "Windows":
        # 常见的 Tesseract Windows 安装包下载地址
        url = "https://github.com/UB-Mannheim/tesseract/wiki"
        try:
            webbrowser.open(url)
            logger.info(f"已打开: {url}")
        except:
            logger.error(f"无法自动打开浏览器，请手动访问: {url}")
    else:
        logger.info("请参考以下命令安装 Tesseract:")
        logger.info("  Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim")
        logger.info("  macOS: brew install tesseract tesseract-lang")


def test_all_engines():
    """测试所有可用 OCR 引擎"""
    print("=" * 60)
    print("OCR 三层回退管理器 - 引擎检测")
    print("=" * 60)
    
    # 检测引擎
    manager = OCRManager()
    
    print(f"\n{manager.status}")
    
    # 查找测试图片
    test_dirs = [
        Path("D:/新建文件夹/待处理图片"),
        Path("D:/新建文件夹/已处理图片"),
        Path(".")
    ]
    
    test_image = None
    for dir_path in test_dirs:
        if dir_path.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                images = list(dir_path.rglob(ext))
                if images:
                    test_image = images[0]
                    break
        if test_image:
            break
    
    if not test_image:
        print("\n未找到测试图片，测试终止")
        return
    
    print(f"\n测试图片: {test_image}")
    print("-" * 60)
    
    # 使用三层回退识别
    result = manager.recognize(str(test_image))
    
    print("\n识别结果:")
    print(f"  成功: {result.get('success')}")
    if result.get('success'):
        print(f"  使用引擎: {result.get('engine_name')}")
        print(f"  文字长度: {len(result.get('text', ''))} 字符")
        text = result.get('text', '')[:300]
        print(f"  前 300 字:\n{text}")
    else:
        print(f"  错误: {result.get('error')}")


if __name__ == "__main__":
    test_all_engines()
