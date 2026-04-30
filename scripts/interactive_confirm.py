#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P2-3 交互式确认模块
提供低置信度分类确认、冲突解决等交互功能
"""

import sys
import io
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass

# 修复 Windows 控制台编码 (只在需要时修复)
if sys.platform == 'win32':
    try:
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # 忽略编码修复失败


@dataclass
class CategoryCandidate:
    """分类候选"""
    category: str
    confidence: float
    keywords: List[str] = None


class InteractiveConfirm:
    """交互式确认"""
    
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
    }
    
    def __init__(self, auto_confirm: bool = False):
        self.auto_confirm = auto_confirm
    
    def _color(self, text: str, color: str) -> str:
        """添加颜色"""
        if not sys.stdout.isatty():
            return text
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"
    
    def _print_box(self, lines: List[str], title: str = None):
        """打印带边框的框"""
        width = 60
        
        # 顶部边框
        print("┌" + "─" * (width - 2) + "┐")
        
        # 标题
        if title:
            padding = (width - 4 - len(title)) // 2
            print(f"│{' ' * padding}{self._color(title, 'bold')}{' ' * (width - 4 - padding - len(title))}│")
            print("├" + "─" * (width - 2) + "┤")
        
        # 内容
        for line in lines:
            if len(line) > width - 4:
                # 拆分过长的行
                while len(line) > width - 4:
                    print(f"│ {line[:width - 4]}{' ' * (width - 5 - len(line[:width - 4]))} │")
                    line = line[width - 4:]
            print(f"│ {line}{' ' * (width - 3 - len(line))} │")
        
        # 底部边框
        print("└" + "─" * (width - 2) + "┘")
    
    def confirm_category(
        self,
        filename: str,
        content_preview: str,
        candidates: List[CategoryCandidate],
        threshold: float = 0.5
    ) -> Optional[str]:
        """
        确认分类
        
        Args:
            filename: 文件名
            content_preview: 内容预览（前50字）
            candidates: 分类候选列表
            threshold: 置信度阈值
        
        Returns:
            确认的分类名称，或 None 表示跳过
        """
        # 检查是否需要确认
        if not candidates:
            return None
        
        top_confidence = candidates[0].confidence if candidates else 0
        
        # 如果最高置信度高于阈值且只有一个候选，自动确认
        if top_confidence >= threshold and len(candidates) == 1:
            return candidates[0].category
        
        # 自动确认模式
        if self.auto_confirm:
            return candidates[0].category if candidates else None
        
        # 构建确认界面
        lines = [
            self._color("📊 分类确认", 'bold'),
            "",
            f"文件: {filename}",
            f"内容预览: {content_preview[:40]}..." if len(content_preview) > 40 else f"内容预览: {content_preview}",
            "",
            f"最高置信度: {top_confidence:.0%}" + (" (较低)" if top_confidence < threshold else ""),
            "",
            self._color("候选分类:", 'white'),
        ]
        
        # 添加候选分类
        for i, candidate in enumerate(candidates[:5], 1):  # 最多显示5个
            confidence_str = f"({candidate.confidence:.0%})"
            if candidate.confidence >= threshold:
                lines.append(f"  [{i}] {candidate.category} {self._color(confidence_str, 'green')}")
            else:
                lines.append(f"  [{i}] {candidate.category} {self._color(confidence_str, 'yellow')}")
            
            # 显示匹配关键词
            if candidate.keywords:
                kw_str = ", ".join(candidate.keywords[:3])
                lines.append(f"      匹配: {kw_str}")
        
        lines.extend([
            "",
            self._color("请选择 [1-5/手动输入/s=跳过]:", 'cyan'),
        ])
        
        self._print_box(lines, "分类确认")
        
        # 获取用户输入
        while True:
            choice = input("请选择: ").strip().lower()
            
            # 跳过
            if choice in ['s', 'skip', '跳过', 'n', 'no']:
                return None
            
            # 数字选择
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(candidates):
                    return candidates[idx].category
                print("无效选择，请重试")
            except ValueError:
                # 手动输入分类名称
                if choice:
                    return choice
                print("请输入数字或分类名称")
    
    def confirm_action(
        self,
        action: str,
        details: str = None,
        options: List[Tuple[str, str]] = None
    ) -> str:
        """
        确认操作
        
        Args:
            action: 操作描述
            details: 详细信息
            options: 选项列表 [(key, description), ...]
        
        Returns:
            选择的选项键
        """
        lines = [
            self._color(f"⚠️ {action}", 'yellow'),
        ]
        
        if details:
            lines.append("")
            lines.append(details)
        
        if options:
            lines.append("")
            for key, desc in options:
                lines.append(f"  [{key}] {desc}")
        
        lines.append("")
        lines.append(f"{self._color('确认操作? [y/n]:', 'cyan')}")
        
        self._print_box(lines, "操作确认")
        
        # 获取确认
        while True:
            choice = input().strip().lower()
            if choice in ['y', 'yes', '是', '']:
                return 'y'
            if choice in ['n', 'no', '否']:
                return 'n'
            print("请输入 y 或 n")
    
    def show_processing_summary(
        self,
        total: int,
        succeeded: int,
        failed: int,
        skipped: int,
        duration: float,
        errors: List[str] = None
    ):
        """显示处理摘要"""
        lines = [
            self._color("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", 'green'),
            self._color("                    处理完成", 'green'),
            self._color("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", 'green'),
            "",
            f"  总数量:     {total}",
            f"  成功:     {self._color(str(succeeded), 'green')}",
            f"  失败:     {self._color(str(failed), 'red')}" if failed > 0 else f"  失败:     {failed}",
            f"  跳过:     {self._color(str(skipped), 'yellow')}" if skipped > 0 else f"  跳过:     {skipped}",
            "",
            f"  耗时:     {duration:.1f} 秒",
        ]
        
        if errors and len(errors) > 0:
            lines.append("")
            lines.append(self._color("  错误列表:", 'red'))
            for error in errors[:5]:  # 最多显示5个
                lines.append(f"    • {error}")
            if len(errors) > 5:
                lines.append(f"    ... 还有 {len(errors) - 5} 个错误")
        
        self._print_box(lines, "处理摘要")
    
    def select_documents(
        self,
        documents: List[Tuple[str, str, int]],
        multi_select: bool = False
    ) -> List[str]:
        """
        选择文档
        
        Args:
            documents: 文档列表 [(name, description, item_count), ...]
            multi_select: 是否允许多选
        
        Returns:
            选中的文档名称列表
        """
        lines = [
            self._color("📁 文档选择", 'bold'),
            "",
        ]
        
        if multi_select:
            lines.append("  (多选，用逗号分隔，如: 1,3,5)")
        
        lines.append("")
        
        for i, (name, desc, count) in enumerate(documents, 1):
            lines.append(f"  [{i}] {name}")
            lines.append(f"      {desc} ({count} 项)")
        
        lines.extend([
            "",
            self._color("请选择:", 'cyan'),
        ])
        
        self._print_box(lines, "文档列表")
        
        # 获取选择
        while True:
            choice = input("请选择: ").strip()
            
            if not choice:
                continue
            
            # 解析选择
            selected = []
            for part in choice.split(','):
                part = part.strip()
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(documents):
                        selected.append(documents[idx][0])
                except ValueError:
                    # 直接输入名称
                    if part in [d[0] for d in documents]:
                        selected.append(part)
            
            if selected:
                return selected
            
            print("无效选择，请重试")
    
    def confirm_merge(
        self,
        source: str,
        target: str,
        source_items: int,
        target_items: int
    ) -> bool:
        """确认合并操作"""
        lines = [
            self._color("⚠️ 文档合并确认", 'yellow'),
            "",
            f"  源文档: {source} ({source_items} 项)",
            f"  目标文档: {target} ({target_items} 项)",
            "",
            "  合并后内容将:",
            "  • 从源文档移动到目标文档",
            "  • 保留原文档作为备份",
            "",
            self._color("确认合并? [y/n]:", 'cyan'),
        ]
        
        self._print_box(lines, "合并确认")
        
        while True:
            choice = input().strip().lower()
            if choice in ['y', 'yes', '是', '']:
                return True
            if choice in ['n', 'no', '否']:
                return False
            print("请输入 y 或 n")


def demo():
    """演示函数（非交互式）"""
    print("\n" + "=" * 60)
    print("  P2-3 交互式确认模块 - 演示")
    print("=" * 60)
    
    # 演示1: 分类确认界面展示
    print("\n[1] 分类确认界面展示:")
    candidates = [
        CategoryCandidate("01_抗炎饮食与营养科普.md", 0.65, ["抗炎", "饮食", "金字塔"]),
        CategoryCandidate("03_中医养生与食疗.md", 0.25, ["中医", "养生"]),
        CategoryCandidate("04_日常饮食建议.md", 0.10, ["饮食", "建议"]),
    ]
    
    confirm = InteractiveConfirm()
    
    # 只展示界面，不等待输入
    lines = [
        confirm._color("📊 分类确认", 'bold'),
        "",
        "文件: Screenshot_20250308.jpg",
        "内容预览: 抗炎饮食金字塔：每天摄入足够的Omega-3...",
        "",
        "最高置信度: 65% (较低)",
        "",
        confirm._color("候选分类:", 'white'),
    ]
    
    for i, candidate in enumerate(candidates[:3], 1):
        confidence_str = f"({candidate.confidence:.0%})"
        if candidate.confidence >= 0.5:
            lines.append(f"  [{i}] {candidate.category} {confirm._color(confidence_str, 'green')}")
        else:
            lines.append(f"  [{i}] {candidate.category} {confirm._color(confidence_str, 'yellow')}")
        
        if candidate.keywords:
            kw_str = ", ".join(candidate.keywords[:3])
            lines.append(f"      匹配: {kw_str}")
    
    lines.extend([
        "",
        confirm._color("请选择 [1-3/手动输入/s=跳过]:", 'cyan'),
    ])
    
    confirm._print_box(lines, "分类确认")
    print("  (演示模式，跳过输入)")
    
    # 演示2: 操作确认界面
    print("\n[2] 操作确认界面展示:")
    lines = [
        confirm._color("⚠️ 删除文档", 'yellow'),
        "",
        "将删除以下文档及其所有内容:",
        "  - old_document.md",
        "",
        "  [y] 确认删除",
        "  [n] 取消",
        "",
        confirm._color("确认操作? [y/n]:", 'cyan'),
    ]
    confirm._print_box(lines, "操作确认")
    print("  (演示模式，跳过输入)")
    
    # 演示3: 处理摘要
    print("\n[3] 处理摘要演示:")
    confirm.show_processing_summary(
        total=28,
        succeeded=25,
        failed=1,
        skipped=2,
        duration=125.5,
        errors=["Screenshot_001.jpg: OCR识别失败", "Screenshot_015.jpg: 图片损坏"]
    )
    
    # 演示4: 自动确认模式
    print("\n[4] 自动确认模式演示:")
    auto_confirm = InteractiveConfirm(auto_confirm=True)
    result = auto_confirm.confirm_category(
        filename="test.jpg",
        content_preview="测试内容",
        candidates=candidates,
        threshold=0.5
    )
    print(f"  自动确认结果: {result}")
    print("  (自动确认模式下，直接返回最高置信度分类)")


if __name__ == '__main__':
    demo()
