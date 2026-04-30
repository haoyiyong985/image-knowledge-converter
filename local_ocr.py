#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地 Tesseract OCR 集成模块
无需网络，完全本地运行

安装要求：
1. 安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. 安装 Python 包: pip install pytesseract pillow
3. 下载中文语言包: chi_sim.traineddata
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class LocalOCR:
    """本地 Tesseract OCR 客户端"""
    
    def __init__(self, tesseract_path: str = None, lang: str = 'chi_sim+eng'):
        """
        初始化本地 OCR 客户端
        
        Args:
            tesseract_path: Tesseract 可执行文件路径（可选，自动检测）
            lang: 识别语言，默认中文+英文
        """
        self.lang = lang
        self.tesseract_available = False
        
        try:
            import pytesseract
            self.pytesseract = pytesseract
            
            # 如果指定了路径，设置 tesseract_cmd
            if tesseract_path and os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                logger.info(f"[OK] 使用指定 Tesseract 路径: {tesseract_path}")
            else:
                # 尝试从环境变量获取路径
                env_path = os.getenv('TESSERACT_CMD')
                if env_path and os.path.exists(env_path):
                    pytesseract.pytesseract.tesseract_cmd = env_path
                    logger.info(f"[OK] 使用环境变量 Tesseract 路径: {env_path}")
            
            # 测试 Tesseract 是否可用
            version = pytesseract.get_tesseract_version()
            logger.info(f"[OK] Tesseract 版本: {version}")
            self.tesseract_available = True
            
        except ImportError:
            logger.error("[FAIL] 未安装 pytesseract，请运行: pip install pytesseract")
            raise
        except Exception as e:
            logger.error(f"[FAIL] Tesseract 初始化失败: {e}")
            logger.error("请确保已安装 Tesseract-OCR 引擎")
            logger.error("下载地址: https://github.com/UB-Mannheim/tesseract/wiki")
            raise
    
    def recognize(self, image_path: str) -> Dict:
        """
        识别单张图片中的文字
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            识别结果字典
        """
        if not self.tesseract_available:
            return {
                "success": False,
                "error": "Tesseract 未正确初始化"
            }
        
        try:
            # 打开图片
            image = Image.open(image_path)
            
            # 转换为 RGB（处理各种格式）
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 使用 Tesseract 识别
            text = self.pytesseract.image_to_string(
                image,
                lang=self.lang,
                config='--psm 6'  # 假设是统一的文本块
            )
            
            # 清理文本
            text = text.strip()
            
            return {
                "success": True,
                "image_path": image_path,
                "text": text,
                "text_count": len(text.split('\n')),
                "language": self.lang,
                "engine": "tesseract"
            }
            
        except Exception as e:
            logger.error(f"识别失败 {image_path}: {e}")
            return {
                "success": False,
                "image_path": image_path,
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
        results = []
        total = len(image_paths)
        
        logger.info(f"开始批量识别 {total} 张图片（本地 Tesseract）...")
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"[{i}/{total}] 识别: {Path(image_path).name}")
            result = self.recognize(image_path)
            results.append(result)
        
        # 统计
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"批量识别完成: {success_count}/{total} 成功")
        
        return results
    
    @staticmethod
    def check_installation() -> Dict:
        """
        检查 Tesseract 安装状态
        
        Returns:
            安装状态信息
        """
        result = {
            "installed": False,
            "version": None,
            "path": None,
            "languages": [],
            "message": ""
        }
        
        try:
            import pytesseract
            
            # 优先使用环境变量中的路径
            env_path = os.getenv('TESSERACT_CMD')
            if env_path and os.path.exists(env_path):
                pytesseract.pytesseract.tesseract_cmd = env_path
                result["path"] = env_path
            
            # 尝试获取版本
            version = pytesseract.get_tesseract_version()
            result["installed"] = True
            result["version"] = str(version)
            if not result["path"]:
                result["path"] = pytesseract.pytesseract.tesseract_cmd
            
            # 获取支持的语言
            try:
                langs = pytesseract.get_languages()
                result["languages"] = langs
            except:
                pass
            
            result["message"] = f"Tesseract {version} 已安装"
            
        except ImportError:
            result["message"] = "未安装 pytesseract Python 包"
        except Exception as e:
            result["message"] = f"Tesseract 未安装或配置错误: {e}"
        
        return result


def test_local_ocr():
    """测试本地 OCR 功能"""
    print("=" * 60)
    print("本地 Tesseract OCR 测试")
    print("=" * 60)
    
    # 检查安装状态
    status = LocalOCR.check_installation()
    print(f"\n安装状态: {status['message']}")
    
    if not status['installed']:
        print("\n请先安装 Tesseract:")
        print("1. 下载安装包: https://github.com/UB-Mannheim/tesseract/wiki")
        print("2. 安装时勾选中文语言包 (chi_sim)")
        print("3. 将安装目录添加到系统 PATH")
        print("4. 运行: pip install pytesseract pillow")
        return
    
    print(f"支持语言: {', '.join(status['languages'][:10])}...")
    
    # 测试识别
    try:
        ocr = LocalOCR()
        
        # 查找测试图片
        test_dirs = [
            Path("D:/新建文件夹/待处理图片"),
            Path("D:/新建文件夹/已处理图片"),
            Path(".")
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
            print(f"\n测试图片: {test_image}")
            result = ocr.recognize(str(test_image))
            
            if result['success']:
                print(f"[OK] 识别成功!")
                print(f"文字长度: {len(result['text'])} 字符")
                print(f"前 200 字:\n{result['text'][:200]}...")
            else:
                print(f"[FAIL] 识别失败: {result.get('error')}")
        else:
            print("\n未找到测试图片")
            
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")


if __name__ == "__main__":
    test_local_ocr()
