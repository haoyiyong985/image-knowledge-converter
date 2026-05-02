#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 管理器 - 支持多引擎自动切换
=============================
支持引擎：
  1. 腾讯云 OCR（首选）
  2. 百度 OCR（第一备用）
  3. 本地 Tesseract（第二备用）

功能：
  - 自动检测首选引擎状态
  - 频率限制时自动提示切换备用
  - 弹窗选择备用引擎
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Callable
from enum import Enum
import tkinter as tk
from tkinter import messagebox, simpledialog

# ============================================================
# 加载环境变量配置
# ============================================================
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"[OK] 已加载配置文件: {env_path}")
else:
    print(f"[WARN] 配置文件不存在: {env_path}")
    print("       请复制 .env.example 为 .env 并填入你的 API 密钥")

# ============================================================
# Tesseract 配置
# ============================================================
# 从环境变量读取路径，或使用默认值
TESSERACT_PATH = os.getenv('TESSERACT_PATH', r'C:\Program Files\Tesseract-OCR\tesseract.exe')

# 验证路径并设置环境变量
if os.path.exists(TESSERACT_PATH):
    os.environ['TESSERACT_CMD'] = TESSERACT_PATH
    print(f"[OK] Tesseract 路径已配置: {TESSERACT_PATH}")
else:
    print(f"[WARN] Tesseract 未找到: {TESSERACT_PATH}")

# 导入各 OCR 模块
try:
    from tencent_ocr import TencentOCR
except ImportError:
    TencentOCR = None

try:
    from baidu_ocr import BaiduOCR
except ImportError:
    BaiduOCR = None

try:
    from local_ocr import LocalOCR
except ImportError:
    LocalOCR = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class OCREngine(Enum):
    """OCR 引擎枚举"""
    TENCENT = "腾讯云 OCR"
    BAIDU = "百度 OCR"
    LOCAL = "本地 Tesseract"


class OCRManager:
    """OCR 管理器"""
    
    def __init__(self):
        self.current_engine: Optional[OCREngine] = None
        self.ocr_client = None
        self.engine_status = {}
        
        # 检查各引擎可用性
        self._check_engines()
    
    def _check_engines(self):
        """检查各 OCR 引擎的可用性"""
        # 检查腾讯云 OCR
        self.engine_status[OCREngine.TENCENT] = self._check_tencent()
        
        # 检查百度 OCR
        self.engine_status[OCREngine.BAIDU] = self._check_baidu()
        
        # 检查本地 Tesseract
        self.engine_status[OCREngine.LOCAL] = self._check_local()
    
    def _check_tencent(self) -> Dict:
        """检查腾讯云 OCR 配置"""
        secret_id = os.getenv('TENCENT_SECRET_ID')
        secret_key = os.getenv('TENCENT_SECRET_KEY')
        
        if secret_id and secret_key and TencentOCR:
            return {
                "available": True,
                "message": "已配置",
                "credentials": True
            }
        return {
            "available": False,
            "message": "未配置 API 密钥",
            "credentials": False
        }
    
    def _check_baidu(self) -> Dict:
        """检查百度 OCR 配置"""
        app_id = os.getenv('BAIDU_APP_ID')
        api_key = os.getenv('BAIDU_API_KEY')
        secret_key = os.getenv('BAIDU_SECRET_KEY')
        
        if all([app_id, api_key, secret_key]) and BaiduOCR:
            return {
                "available": True,
                "message": "已配置",
                "credentials": True
            }
        return {
            "available": False,
            "message": "未配置 API 密钥",
            "credentials": False
        }
    
    def _check_local(self) -> Dict:
        """检查本地 Tesseract"""
        if LocalOCR:
            status = LocalOCR.check_installation()
            return {
                "available": status["installed"],
                "message": status["message"],
                "version": status.get("version")
            }
        return {
            "available": False,
            "message": "未安装 local_ocr 模块"
        }
    
    def init_engine(self, engine: OCREngine) -> bool:
        """
        初始化指定引擎
        
        Args:
            engine: OCR 引擎类型
            
        Returns:
            是否初始化成功
        """
        try:
            if engine == OCREngine.TENCENT and TencentOCR:
                self.ocr_client = TencentOCR()
                self.current_engine = engine
                logger.info(f"[OK] 已切换到: {engine.value}")
                return True
                
            elif engine == OCREngine.BAIDU and BaiduOCR:
                self.ocr_client = BaiduOCR()
                self.current_engine = engine
                logger.info(f"[OK] 已切换到: {engine.value}")
                return True
                
            elif engine == OCREngine.LOCAL and LocalOCR:
                self.ocr_client = LocalOCR()
                self.current_engine = engine
                logger.info(f"[OK] 已切换到: {engine.value}")
                return True
                
        except Exception as e:
            logger.error(f"[FAIL] 初始化 {engine.value} 失败: {e}")
            return False
        
        return False
    
    def auto_select_engine(self) -> Optional[OCREngine]:
        """
        自动选择可用的引擎（按优先级）
        
        Returns:
            选中的引擎，如果没有可用引擎返回 None
        """
        # 优先级：腾讯云 > 百度 > 本地
        priority = [OCREngine.TENCENT, OCREngine.BAIDU, OCREngine.LOCAL]
        
        for engine in priority:
            if self.engine_status[engine]["available"]:
                if self.init_engine(engine):
                    return engine
        
        return None
    
    def show_engine_selection_dialog(self, reason: str = "") -> Optional[OCREngine]:
        """
        显示引擎选择弹窗
        
        Args:
            reason: 显示选择原因（如频率限制）
            
        Returns:
            用户选择的引擎，如果取消返回 None
        """
        # 创建主窗口（隐藏）
        root = tk.Tk()
        root.withdraw()
        
        # 构建提示信息
        message = "请选择 OCR 引擎:\n\n"
        
        if reason:
            message = f"⚠️ {reason}\n\n请选择其他 OCR 引擎:\n\n"
        
        # 显示各引擎状态
        for engine in OCREngine:
            status = self.engine_status[engine]
            status_icon = "✓" if status["available"] else "✗"
            message += f"{status_icon} {engine.value}: {status['message']}\n"
        
        message += "\n请选择（输入数字）:\n"
        message += "1 - 腾讯云 OCR\n"
        message += "2 - 百度 OCR\n"
        message += "3 - 本地 Tesseract\n"
        message += "0 - 取消"
        
        # 显示选择对话框
        choice = simpledialog.askstring(
            "选择 OCR 引擎",
            message,
            parent=root
        )
        
        root.destroy()
        
        if choice is None or choice == "0":
            return None
        
        # 解析选择
        choice_map = {
            "1": OCREngine.TENCENT,
            "2": OCREngine.BAIDU,
            "3": OCREngine.LOCAL
        }
        
        selected = choice_map.get(choice.strip())
        
        if selected and self.engine_status[selected]["available"]:
            return selected
        elif selected:
            # 选择的引擎不可用，提示
            root = tk.Tk()
            root.withdraw()
            messagebox.showwarning(
                "引擎不可用",
                f"{selected.value} 未配置或不可用，请选择其他引擎。"
            )
            root.destroy()
            return self.show_engine_selection_dialog(reason)
        
        return None
    
    def recognize(self, image_path: str) -> Dict:
        """
        识别单张图片
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别结果
        """
        if not self.ocr_client:
            # 尝试自动选择引擎
            engine = self.auto_select_engine()
            if not engine:
                return {
                    "success": False,
                    "error": "没有可用的 OCR 引擎，请先配置"
                }
        
        try:
            result = self.ocr_client.recognize(image_path)
            
            # 检查是否是频率限制错误
            if not result.get("success"):
                error = result.get("error", "")
                if "频率" in error or "limit" in error.lower() or "quota" in error.lower():
                    logger.warning(f"[WARN] {self.current_engine.value} 达到频率限制")
                    
                    # 显示弹窗让用户选择备用引擎
                    new_engine = self.show_engine_selection_dialog(
                        f"{self.current_engine.value} 达到频率限制"
                    )
                    
                    if new_engine and self.init_engine(new_engine):
                        # 使用新引擎重新识别
                        return self.ocr_client.recognize(image_path)
                    else:
                        result["need_switch"] = True
                        result["switch_reason"] = "频率限制"
            
            return result
            
        except Exception as e:
            logger.error(f"识别失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def recognize_batch(self, image_paths: List[str]) -> List[Dict]:
        """
        批量识别图片
        
        Args:
            image_paths: 图片路径列表
            
        Returns:
            识别结果列表
        """
        if not self.ocr_client:
            engine = self.auto_select_engine()
            if not engine:
                return [{"success": False, "error": "没有可用的 OCR 引擎"} for _ in image_paths]
        
        results = []
        total = len(image_paths)
        
        logger.info(f"开始批量识别 {total} 张图片（{self.current_engine.value}）...")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"[{i}/{total}] 识别: {Path(image_path).name}")
            
            result = self.recognize(image_path)
            results.append(result)
            
            # 检查是否需要切换引擎
            if result.get("need_switch"):
                logger.warning(f"处理中断，需要切换引擎: {result.get('switch_reason')}")
                # 这里可以选择继续处理剩余图片或停止
                # 暂时继续，让用户在弹窗中选择
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"批量识别完成: {success_count}/{total} 成功")
        
        return results
    
    def get_current_engine(self) -> Optional[str]:
        """获取当前使用的引擎名称"""
        if self.current_engine:
            return self.current_engine.value
        return None


def test_ocr_manager():
    """测试 OCR 管理器"""
    print("=" * 60)
    print("OCR 管理器测试")
    print("=" * 60)
    
    manager = OCRManager()
    
    # 显示引擎状态
    print("\n引擎状态:")
    for engine in OCREngine:
        status = manager.engine_status[engine]
        icon = "[OK]" if status["available"] else "[FAIL]"
        print(f"  {icon} {engine.value}: {status['message']}")
    
    # 自动选择引擎
    print("\n自动选择引擎...")
    engine = manager.auto_select_engine()
    
    if engine:
        print(f"[OK] 已选择: {engine.value}")
        
        # 测试识别（如果有图片）
        test_dirs = [
            Path("D:/新建文件夹/已处理图片"),
            Path("D:/新建文件夹/待处理图片")
        ]
        
        test_image = None
        for dir_path in test_dirs:
            if dir_path.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png']:
                    images = list(dir_path.rglob(ext))
                    if images:
                        test_image = images[0]
                        break
            if test_image:
                break
        
        if test_image and test_image.exists():
            print(f"\n测试识别: {test_image.name}")
            result = manager.recognize(str(test_image))
            
            if result['success']:
                print(f"[OK] 识别成功!")
                print(f"  文字长度: {len(result['text'])} 字符")
                print(f"  前 100 字: {result['text'][:100]}...")
            else:
                print(f"[FAIL] 识别失败: {result.get('error')}")
        else:
            print("\n未找到测试图片")
    else:
        print("[FAIL] 没有可用的 OCR 引擎")
        print("\n请至少配置一个引擎:")
        print("  1. 腾讯云: 设置 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")
        print("  2. 百度: 设置 BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY")
        print("  3. 本地: 安装 Tesseract 和 pytesseract")


if __name__ == "__main__":
    test_ocr_manager()
