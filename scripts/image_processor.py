#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理模块 - 负责图片预处理、OCR文字提取和表格检测
"""

import os
import cv2
import numpy as np
import pytesseract
from PIL import Image
import logging
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """OCR结果数据类"""
    text: str
    confidence: float
    boxes: List[Tuple[int, int, int, int]]
    language: str
    processing_time: float


@dataclass
class TableData:
    """表格数据类"""
    headers: List[str]
    rows: List[List[str]]
    confidence: float
    bbox: Tuple[int, int, int, int]


@dataclass
class ProcessedImage:
    """处理后的图片数据类"""
    original_path: str
    processed_path: Optional[str]
    ocr_result: Optional[OCRResult]
    tables: List[TableData]
    metadata: Dict
    timestamp: datetime


class ImagePreprocessor:
    """图片预处理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
    def preprocess(self, image_path: str) -> np.ndarray:
        """
        对图片进行预处理
        
        Args:
            image_path: 图片路径
            
        Returns:
            预处理后的图片数组
        """
        logger.info(f"开始预处理图片: {image_path}")
        
        # 读取图片
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法读取图片: {image_path}")
        
        # 调整图片大小（如果太大）
        image = self._resize_if_needed(image)
        
        # 自动旋转
        image = self._auto_rotate(image)
        
        # 转换为灰度图
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 对比度增强
        enhanced = self._enhance_contrast(gray)
        
        # 去噪
        denoised = self._denoise(enhanced)
        
        # 二值化
        binary = self._binarize(denoised)
        
        logger.info("图片预处理完成")
        return binary
    
    def _resize_if_needed(self, image: np.ndarray) -> np.ndarray:
        """调整图片大小"""
        max_width = self.config.get('max_width', 4096)
        max_height = self.config.get('max_height', 4096)
        
        height, width = image.shape[:2]
        
        if width > max_width or height > max_height:
            scale = min(max_width / width, max_height / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"图片已调整大小: {width}x{height} -> {new_width}x{new_height}")
        
        return image
    
    def _auto_rotate(self, image: np.ndarray) -> np.ndarray:
        """自动检测并旋转图片"""
        if not self.config.get('auto_rotate', True):
            return image
        
        try:
            # 使用Tesseract检测方向
            osd = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
            rotation = osd.get('rotate', 0)
            
            if rotation != 0:
                logger.info(f"检测到图片需要旋转: {rotation}度")
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, rotation, 1.0)
                image = cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        except Exception as e:
            logger.warning(f"自动旋转检测失败: {e}")
        
        return image
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """增强对比度"""
        if not self.config.get('contrast_enhancement', True):
            return image
        
        # 使用CLAHE（对比度受限的自适应直方图均衡化）
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        
        return enhanced
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """去噪处理"""
        if not self.config.get('denoise', True):
            return image
        
        # 使用双边滤波去噪
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        
        return denoised
    
    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """二值化处理"""
        if not self.config.get('binarize', True):
            return image
        
        # 自适应阈值二值化
        binary = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary


class TextExtractor:
    """文字提取器"""
    
    def __init__(self, language: str = 'chi_sim+eng'):
        self.language = language
        
    def extract(self, image: np.ndarray) -> OCRResult:
        """
        从图片中提取文字
        
        Args:
            image: 预处理后的图片数组
            
        Returns:
            OCR结果
        """
        import time
        start_time = time.time()
        
        logger.info("开始OCR文字提取")
        
        try:
            # 获取详细OCR数据
            data = pytesseract.image_to_data(
                image, 
                lang=self.language,
                output_type=pytesseract.Output.DICT
            )
            
            # 提取文本和位置信息
            texts = []
            boxes = []
            confidences = []
            
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                conf = int(data['conf'][i])
                if conf > 30:  # 过滤低置信度结果
                    text = data['text'][i].strip()
                    if text:
                        texts.append(text)
                        confidences.append(conf)
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                        boxes.append((x, y, x+w, y+h))
            
            # 合并文本
            full_text = ' '.join(texts)
            
            # 计算平均置信度
            avg_confidence = np.mean(confidences) if confidences else 0
            
            processing_time = time.time() - start_time
            
            result = OCRResult(
                text=full_text,
                confidence=avg_confidence,
                boxes=boxes,
                language=self.language,
                processing_time=processing_time
            )
            
            logger.info(f"OCR完成: 提取了 {len(texts)} 个文本块, 平均置信度: {avg_confidence:.2f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"OCR提取失败: {e}")
            raise


class TableDetector:
    """表格检测器"""
    
    def __init__(self, min_table_area: int = 10000):
        self.min_table_area = min_table_area
        
    def detect_tables(self, image: np.ndarray) -> List[TableData]:
        """
        检测图片中的表格
        
        Args:
            image: 原始图片数组
            
        Returns:
            检测到的表格列表
        """
        logger.info("开始检测表格")
        
        tables = []
        
        try:
            # 转换为灰度图
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image
            
            # 二值化
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            
            # 检测水平和垂直线
            horizontal = self._detect_lines(binary, 'horizontal')
            vertical = self._detect_lines(binary, 'vertical')
            
            # 合并线条
            table_mask = cv2.addWeighted(horizontal, 0.5, vertical, 0.5, 0.0)
            
            # 查找表格轮廓
            contours, _ = cv2.findContours(
                table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                if area < self.min_table_area:
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # 提取表格区域
                table_roi = image[y:y+h, x:x+w]
                
                # 提取表格数据
                table_data = self._extract_table_data(table_roi, (x, y, w, h))
                
                if table_data:
                    tables.append(table_data)
                    logger.info(f"检测到表格 {i+1}: 位置({x}, {y}), 大小({w}x{h})")
            
            logger.info(f"表格检测完成: 共检测到 {len(tables)} 个表格")
            
        except Exception as e:
            logger.error(f"表格检测失败: {e}")
        
        return tables
    
    def _detect_lines(self, binary: np.ndarray, direction: str) -> np.ndarray:
        """检测线条"""
        if direction == 'horizontal':
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        else:
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
        
        return lines
    
    def _extract_table_data(self, table_roi: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[TableData]:
        """提取表格数据"""
        try:
            # 使用OCR提取表格中的文字
            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(table_roi, config=custom_config)
            
            # 简单解析表格（按行分割）
            lines = text.strip().split('\n')
            rows = []
            
            for line in lines:
                # 按空格或多个空格分割
                cells = [cell.strip() for cell in line.split() if cell.strip()]
                if cells:
                    rows.append(cells)
            
            if len(rows) < 2:
                return None
            
            # 假设第一行是表头
            headers = rows[0]
            data_rows = rows[1:]
            
            return TableData(
                headers=headers,
                rows=data_rows,
                confidence=70.0,
                bbox=bbox
            )
            
        except Exception as e:
            logger.error(f"提取表格数据失败: {e}")
            return None


class ImageProcessor:
    """图片处理器主类"""
    
    def __init__(self, config_path: str = None):
        """
        初始化图片处理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.preprocessor = ImagePreprocessor(self.config.get('preprocessing', {}))
        self.text_extractor = TextExtractor(self.config.get('ocr', {}).get('language', 'chi_sim+eng'))
        self.table_detector = TableDetector(
            self.config.get('ocr', {}).get('table_detection', {}).get('min_table_area', 10000)
        )
        
    def _load_config(self, config_path: str = None) -> Dict:
        """加载配置"""
        default_config = {
            'preprocessing': {
                'auto_rotate': True,
                'grayscale': True,
                'contrast_enhancement': True,
                'denoise': True,
                'binarize': True,
                'max_width': 4096,
                'max_height': 4096
            },
            'ocr': {
                'language': 'chi_sim+eng',
                'table_detection': {
                    'enabled': True,
                    'min_table_area': 10000
                }
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    default_config.update(config)
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}, 使用默认配置")
        
        return default_config
    
    def process_image(self, image_path: str, output_dir: str = None) -> ProcessedImage:
        """
        处理单张图片
        
        Args:
            image_path: 图片路径
            output_dir: 输出目录
            
        Returns:
            处理后的图片数据
        """
        logger.info(f"开始处理图片: {image_path}")
        
        try:
            # 预处理
            preprocessed = self.preprocessor.preprocess(image_path)
            
            # 保存预处理后的图片
            processed_path = None
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                basename = os.path.splitext(os.path.basename(image_path))[0]
                processed_path = os.path.join(output_dir, f"{basename}_processed.png")
                cv2.imwrite(processed_path, preprocessed)
            
            # 文字提取
            ocr_result = self.text_extractor.extract(preprocessed)
            
            # 表格检测
            original_image = cv2.imread(image_path)
            tables = self.table_detector.detect_tables(original_image)
            
            # 构建元数据
            metadata = {
                'filename': os.path.basename(image_path),
                'file_size': os.path.getsize(image_path),
                'image_dimensions': original_image.shape[:2],
                'text_length': len(ocr_result.text),
                'table_count': len(tables)
            }
            
            result = ProcessedImage(
                original_path=image_path,
                processed_path=processed_path,
                ocr_result=ocr_result,
                tables=tables,
                metadata=metadata,
                timestamp=datetime.now()
            )
            
            logger.info(f"图片处理完成: {image_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"处理图片失败 {image_path}: {e}")
            raise
    
    def process_batch(self, image_paths: List[str], output_dir: str = None) -> List[ProcessedImage]:
        """
        批量处理图片
        
        Args:
            image_paths: 图片路径列表
            output_dir: 输出目录
            
        Returns:
            处理后的图片数据列表
        """
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"处理第 {i}/{len(image_paths)} 张图片")
            try:
                result = self.process_image(image_path, output_dir)
                results.append(result)
            except Exception as e:
                logger.error(f"处理失败: {image_path}, 错误: {e}")
        
        return results
    
    def save_results(self, result: ProcessedImage, output_dir: str, formats: List[str] = None):
        """
        保存处理结果
        
        Args:
            result: 处理后的图片数据
            output_dir: 输出目录
            formats: 输出格式列表
        """
        if formats is None:
            formats = ['txt', 'json']
        
        os.makedirs(output_dir, exist_ok=True)
        basename = os.path.splitext(os.path.basename(result.original_path))[0]
        
        # 保存文本
        if 'txt' in formats and result.ocr_result:
            txt_path = os.path.join(output_dir, f"{basename}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(result.ocr_result.text)
            logger.info(f"文本已保存: {txt_path}")
        
        # 保存JSON
        if 'json' in formats:
            json_path = os.path.join(output_dir, f"{basename}.json")
            data = {
                'original_path': result.original_path,
                'timestamp': result.timestamp.isoformat(),
                'metadata': result.metadata,
                'text': result.ocr_result.text if result.ocr_result else '',
                'confidence': result.ocr_result.confidence if result.ocr_result else 0,
                'tables': [
                    {
                        'headers': t.headers,
                        'rows': t.rows,
                        'confidence': t.confidence
                    }
                    for t in result.tables
                ]
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON已保存: {json_path}")
        
        # 保存表格为CSV
        for i, table in enumerate(result.tables):
            csv_path = os.path.join(output_dir, f"{basename}_table_{i+1}.csv")
            import csv
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(table.headers)
                writer.writerows(table.rows)
            logger.info(f"表格已保存: {csv_path}")


if __name__ == '__main__':
    # 测试代码
    processor = ImageProcessor()
    
    # 测试图片路径
    test_image = "test_image.png"
    
    if os.path.exists(test_image):
        result = processor.process_image(test_image, "output")
        processor.save_results(result, "output", ['txt', 'json'])
        print(f"处理完成: {result.original_path}")
        print(f"提取文本长度: {len(result.ocr_result.text)}")
        print(f"检测到表格数: {len(result.tables)}")
    else:
        print(f"测试图片不存在: {test_image}")
