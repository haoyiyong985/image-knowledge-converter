#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P2-2 进度条和日志系统
提供实时进度反馈和结构化日志记录
"""

import sys
import os
import io
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field
from enum import Enum

# 修复 Windows 控制台编码 (只在需要时修复)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # 忽略编码修复失败


class LogLevel(Enum):
    """日志级别"""
    DEBUG = 10
    INFO = 20
    SUCCESS = 25  # 自定义成功级别
    WARNING = 30
    ERROR = 40


@dataclass
class LogEntry:
    """日志条目"""
    timestamp: str
    level: str
    message: str
    details: Optional[str] = None


class ProgressBar:
    """进度条组件"""
    
    def __init__(
        self,
        total: int,
        prefix: str = "处理中",
        width: int = 40,
        show_percent: bool = True,
        show_count: bool = True,
        show_current: bool = False,
        current_text: str = ""
    ):
        self.total = total
        self.current = 0
        self.prefix = prefix
        self.width = width
        self.show_percent = show_percent
        self.show_count = show_count
        self.show_current = show_current
        self.current_text = current_text
        self.start_time = time.time()
        self._last_line_len = 0
    
    @property
    def percent(self) -> float:
        """计算百分比"""
        if self.total == 0:
            return 0
        return self.current / self.total
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def eta(self) -> Optional[float]:
        """预计剩余时间（秒）"""
        if self.current == 0:
            return None
        rate = self.current / self.elapsed_time
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else 0
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds is None:
            return "--:--"
        if seconds < 60:
            return f"{int(seconds)}秒"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def _render(self) -> str:
        """渲染进度条"""
        # 计算填充宽度
        filled = int(self.width * self.percent)
        empty = self.width - filled
        
        # 构建进度条
        bar = f"[{'█' * filled}{'░' * empty}]"
        
        # 构建前缀
        parts = [f"{self.prefix}"]
        
        # 百分比
        if self.show_percent:
            parts.append(f"{self.percent:.0%}")
        
        # 计数
        if self.show_count:
            parts.append(f"已处理: {self.current}/{self.total}")
        
        # 当前文件名
        if self.show_current and self.current_text:
            # 截断过长文件名
            text = self.current_text
            if len(text) > 30:
                text = text[:27] + "..."
            parts.append(f"当前: {text}")
        
        # 预计剩余时间
        eta = self._format_time(self.eta)
        parts.append(f"预计剩余: {eta}")
        
        return f"{bar} {' | '.join(parts)}"
    
    def update(self, current: int = None, current_text: str = None):
        """更新进度"""
        if current is not None:
            self.current = current
        if current_text is not None:
            self.current_text = current_text
        
        # 打印进度条（覆盖上一行）
        line = self._render()
        # 清除上一行
        clear_line = '\r' + ' ' * self._last_line_len + '\r'
        sys.stdout.write(clear_line + line)
        sys.stdout.flush()
        self._last_line_len = len(line)
    
    def increment(self, current_text: str = None):
        """增加进度"""
        self.current += 1
        if current_text:
            self.current_text = current_text
        self.update()
    
    def finish(self, message: str = "完成"):
        """完成进度条"""
        self.current = self.total
        line = self._render() + f" ✓ {message}"
        clear_line = '\r' + ' ' * self._last_line_len + '\r'
        sys.stdout.write(clear_line + line + '\n')
        sys.stdout.flush()
        self._last_line_len = 0


class StructuredLogger:
    """结构化日志记录器"""
    
    COLORS = {
        'reset': '\033[0m',
        'black': '\033[30m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'gray': '\033[90m',
    }
    
    LEVEL_COLORS = {
        'DEBUG': 'gray',
        'INFO': 'blue',
        'SUCCESS': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
    }
    
    def __init__(self, name: str = "converter", log_dir: str = "logs", level: int = logging.INFO):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = level
        self.entries: List[LogEntry] = []
        
        # 设置文件日志
        self._setup_file_logger()
    
    def _setup_file_logger(self):
        """设置文件日志"""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.level)
        
        # 避免重复添加 handler
        if self.logger.handlers:
            return
        
        # 文件 handler
        log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    def _color(self, text: str, color: str) -> str:
        """添加颜色"""
        if not sys.stdout.isatty():
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _get_timestamp(self) -> str:
        """获取时间戳"""
        return datetime.now().strftime('%H:%M:%S')
    
    def _log(self, level: str, message: str, details: str = None, color_output: bool = True):
        """记录日志"""
        entry = LogEntry(
            timestamp=self._get_timestamp(),
            level=level,
            message=message,
            details=details
        )
        self.entries.append(entry)
        
        # 确定颜色
        color = self.LEVEL_COLORS.get(level, 'white')
        
        # 构建输出
        if details:
            output = f"[{entry.timestamp}] {level:8} {message}"
            if color_output:
                output = self._color(output, color)
            print(output)
            print(f"              {details}")
        else:
            output = f"[{entry.timestamp}] {level:8} {message}"
            if color_output:
                output = self._color(output, color)
            print(output)
        
        # 记录到文件
        if details:
            self.logger.log(
                getattr(logging, level, logging.INFO),
                f"{message} | {details}"
            )
        else:
            self.logger.log(
                getattr(logging, level, logging.INFO),
                message
            )
    
    def debug(self, message: str, details: str = None):
        """调试日志"""
        self._log('DEBUG', message, details)
    
    def info(self, message: str, details: str = None):
        """信息日志"""
        self._log('INFO', message, details)
    
    def success(self, message: str, details: str = None):
        """成功日志"""
        self._log('SUCCESS', message, details)
    
    def warning(self, message: str, details: str = None):
        """警告日志"""
        self._log('WARNING', message, details)
    
    def error(self, message: str, details: str = None):
        """错误日志"""
        self._log('ERROR', message, details)
    
    def section(self, title: str):
        """章节标题"""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print('=' * 60)
    
    def divider(self):
        """分隔线"""
        print('-' * 60)
    
    def get_summary(self) -> dict:
        """获取日志摘要"""
        summary = {
            'total': len(self.entries),
            'by_level': {},
            'duration': None
        }
        
        for entry in self.entries:
            level = entry.level
            summary['by_level'][level] = summary['by_level'].get(level, 0) + 1
        
        if self.entries:
            start = datetime.strptime(self.entries[0].timestamp, '%H:%M:%S')
            end = datetime.strptime(self.entries[-1].timestamp, '%H:%M:%S')
            summary['duration'] = (end - start).total_seconds()
        
        return summary
    
    def print_summary(self):
        """打印日志摘要"""
        summary = self.get_summary()
        
        print(f"\n{'=' * 60}")
        print("  日志摘要")
        print('=' * 60)
        print(f"  总日志条目: {summary['total']}")
        
        for level, count in sorted(summary['by_level'].items()):
            color = self.LEVEL_COLORS.get(level, 'white')
            print(f"  {self._color(level + ':', color)} {count}")
        
        if summary['duration']:
            print(f"  总耗时: {summary['duration']:.1f} 秒")


class BatchProgressTracker:
    """批量处理进度追踪器"""
    
    def __init__(self, total: int, name: str = "批量处理"):
        self.total = total
        self.name = name
        self.current = 0
        self.succeeded = 0
        self.failed = 0
        self.skipped = 0
        self.logger = StructuredLogger(name="batch")
        self.progress_bar = ProgressBar(
            total=total,
            prefix=name,
            show_current=True
        )
    
    def start(self):
        """开始处理"""
        self.logger.section(f"{self.name} - 开始")
        self.logger.info(f"总数量: {self.total}")
        self.progress_bar.update(0)
    
    def update(self, filename: str = "", success: bool = True, message: str = ""):
        """更新进度"""
        self.current += 1
        if success:
            self.succeeded += 1
        else:
            self.failed += 1
        
        self.progress_bar.update(self.current, filename)
        
        if message:
            self.logger.info(message)
    
    def skip(self, filename: str = "", reason: str = ""):
        """跳过项目"""
        self.current += 1
        self.skipped += 1
        self.progress_bar.update(self.current, filename)
        self.logger.warning(f"跳过: {filename}", reason)
    
    def finish(self):
        """完成处理"""
        self.progress_bar.finish()
        
        self.logger.section(f"{self.name} - 完成")
        self.logger.success(f"处理完成!", f"成功: {self.succeeded} | 失败: {self.failed} | 跳过: {self.skipped}")
        
        if self.failed > 0:
            self.logger.warning(f"有 {self.failed} 个项目处理失败，请查看日志")
        
        return {
            'total': self.total,
            'succeeded': self.succeeded,
            'failed': self.failed,
            'skipped': self.skipped
        }


def demo():
    """演示函数"""
    print("\n" + "=" * 60)
    print("  P2-2 进度条和日志系统 - 演示")
    print("=" * 60)
    
    # 演示进度条
    print("\n[1] 进度条演示:")
    bar = ProgressBar(total=20, prefix="处理图片", show_current=True)
    
    for i in range(1, 21):
        time.sleep(0.1)
        filename = f"Screenshot_{i:03d}.jpg"
        bar.update(i, filename)
    
    bar.finish("完成!")
    
    # 演示结构化日志
    print("\n[2] 结构化日志演示:")
    logger = StructuredLogger("demo")
    
    logger.info("开始处理图片")
    logger.debug("调试信息：加载配置")
    logger.success("图片处理成功", "Screenshot_001.jpg -> 文档")
    logger.warning("分类置信度较低", "0.45 < 0.5")
    logger.error("OCR 识别失败", "图片质量过低")
    
    logger.print_summary()
    
    # 演示批量处理追踪器
    print("\n[3] 批量处理追踪器演示:")
    tracker = BatchProgressTracker(total=5, name="测试处理")
    tracker.start()
    
    for i in range(1, 6):
        time.sleep(0.2)
        filename = f"test_{i}.jpg"
        success = i != 3  # 第3个失败
        tracker.update(filename, success, f"处理 {filename}" if success else "")
    
    tracker.finish()


if __name__ == '__main__':
    demo()
