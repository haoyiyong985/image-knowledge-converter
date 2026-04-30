#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模板引擎
========
读取模板配置（YAML），提供统一接口供 generate_word.py 调用。

支持：
- 列出所有可用模板
- 加载指定模板（ID 或名称）
- 创建用户自定义模板
- 根据模板配置格式化 Word 文档样式

用法：
    from template_engine import TemplateEngine

    engine = TemplateEngine()
    tpl = engine.load("minimalist")   # 加载极简模板
    tpl.apply_heading(paragraph, level=2)
    tpl.apply_body(paragraph)
"""

import os
import re
import yaml
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# 模板根目录（相对于 scripts/ 的父级）
_SCRIPT_DIR = Path(__file__).parent
_TEMPLATES_DIR = _SCRIPT_DIR.parent / "image-knowledge-converter" / "assets" / "templates"
_USER_TEMPLATES_DIR = _TEMPLATES_DIR / "user_custom"

# 默认模板 ID
DEFAULT_TEMPLATE_ID = "default"


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """将 6 位十六进制颜色转换为 (r, g, b) 元组"""
    hex_color = hex_color.lstrip("#").upper()
    if len(hex_color) == 6:
        return int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return 0, 0, 0


class TemplateConfig:
    """
    封装单个模板配置，提供方便的读取接口，
    以及将样式应用到 python-docx 段落/表格对象的方法。
    """

    def __init__(self, config: Dict, template_dir: Path):
        self._cfg = config
        self.template_dir = template_dir

        # 基础信息
        tpl = config.get("template", {})
        self.id = tpl.get("id", template_dir.name)
        self.name = tpl.get("name", self.id)
        self.version = tpl.get("version", "1.0")
        self.description = tpl.get("description", "")
        self.author = tpl.get("author", "")

        # 各节配置
        self.format = config.get("format", {})
        self.content = config.get("content", {})
        self.output = config.get("output", {})

    # ------------------------------------------------------------------ #
    # 属性快捷访问
    # ------------------------------------------------------------------ #

    @property
    def title_cfg(self) -> Dict:
        return self.format.get("title", {})

    @property
    def headings_cfg(self) -> Dict:
        return self.format.get("headings", {})

    @property
    def body_cfg(self) -> Dict:
        return self.format.get("body", {})

    @property
    def list_cfg(self) -> Dict:
        return self.format.get("list", {})

    @property
    def table_cfg(self) -> Dict:
        return self.format.get("table", {})

    def heading_level_cfg(self, level: int) -> Dict:
        """返回指定标题层级的配置，level 1-4"""
        key = f"h{min(level, 4)}"
        return self.headings_cfg.get(key, {})

    # ------------------------------------------------------------------ #
    # 应用样式到 python-docx 对象
    # ------------------------------------------------------------------ #

    def apply_heading(self, paragraph, level: int, numbering_counters: Optional[List[int]] = None):
        """
        为标题段落应用模板样式

        Args:
            paragraph: docx Paragraph 对象
            level: 标题层级 (1-4)
            numbering_counters: 自动编号计数器列表（长度 >=4），仅在 auto_numbering=True 时使用
        """
        try:
            from docx.shared import Pt, RGBColor
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            return

        hcfg = self.heading_level_cfg(level)
        font_size = hcfg.get("font_size", 13)
        bold = hcfg.get("bold", True)
        color_hex = hcfg.get("color", "000000")
        space_before = hcfg.get("space_before", 8)
        space_after = hcfg.get("space_after", 4)

        # 自动编号
        if self.headings_cfg.get("auto_numbering", False) and numbering_counters is not None:
            numbering_counters[level - 1] += 1
            for i in range(level, 4):
                numbering_counters[i] = 0
            prefix = ".".join(str(numbering_counters[i]) for i in range(level)) + " "
            if paragraph.runs:
                paragraph.runs[0].text = prefix + paragraph.runs[0].text

        # 段落间距
        pf = paragraph.paragraph_format
        pf.space_before = Pt(space_before)
        pf.space_after = Pt(space_after)

        # 字体样式
        for run in paragraph.runs:
            run.bold = bold
            run.font.size = Pt(font_size)
            r, g, b = _hex_to_rgb(color_hex)
            run.font.color.rgb = RGBColor(r, g, b)

    def apply_title(self, paragraph):
        """为文档主标题段落应用样式"""
        try:
            from docx.shared import Pt
            from docx.enum.text import WD_ALIGN_PARAGRAPH
        except ImportError:
            return

        tcfg = self.title_cfg
        font_size = tcfg.get("font_size", 18)
        bold = tcfg.get("bold", True)
        align_str = tcfg.get("align", "center")
        align_map = {
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
        }
        paragraph.alignment = align_map.get(align_str, WD_ALIGN_PARAGRAPH.CENTER)

        for run in paragraph.runs:
            run.bold = bold
            run.font.size = Pt(font_size)

    def apply_body(self, paragraph):
        """为正文段落应用样式"""
        try:
            from docx.shared import Pt, Cm
            from docx.oxml.ns import qn
            from lxml import etree
        except ImportError:
            return

        bcfg = self.body_cfg
        font_family = bcfg.get("font_family", "微软雅黑")
        font_size = bcfg.get("font_size", 11)
        line_spacing = bcfg.get("line_spacing", 1.5)
        space_after = bcfg.get("space_after", 6)
        first_line_indent = bcfg.get("first_line_indent", False)

        pf = paragraph.paragraph_format
        pf.space_after = Pt(space_after)

        # 行距
        from docx.shared import Pt as _Pt
        from docx.oxml import OxmlElement
        pPr = paragraph._p.get_or_add_pPr()
        spacing = pPr.find(qn("w:spacing"))
        if spacing is None:
            spacing = OxmlElement("w:spacing")
            pPr.append(spacing)
        # 行距用 240 * 倍数（twips，1pt=20twips，单倍=240）
        spacing.set(qn("w:line"), str(int(240 * line_spacing)))
        spacing.set(qn("w:lineRule"), "auto")

        # 首行缩进
        if first_line_indent:
            ind = pPr.find(qn("w:ind"))
            if ind is None:
                ind = OxmlElement("w:ind")
                pPr.append(ind)
            ind.set(qn("w:firstLine"), "480")  # 2字符 = 2*240 twips

        for run in paragraph.runs:
            run.font.size = Pt(font_size)
            run.font.name = font_family
            # 设置中文字体
            rPr = run._r.get_or_add_rPr()
            rFonts = rPr.find(qn("w:rFonts"))
            if rFonts is None:
                rFonts = OxmlElement("w:rFonts")
                rPr.insert(0, rFonts)
            rFonts.set(qn("w:eastAsia"), font_family)

    def apply_list(self, paragraph):
        """为列表项段落应用样式"""
        try:
            from docx.shared import Pt
        except ImportError:
            return

        lcfg = self.list_cfg
        font_size = lcfg.get("font_size", 11)
        space_after = lcfg.get("space_after", 3)

        pf = paragraph.paragraph_format
        pf.space_after = Pt(space_after)

        for run in paragraph.runs:
            run.font.size = Pt(font_size)

    def apply_table(self, table):
        """
        为 Word 表格应用模板样式

        Args:
            table: docx Table 对象
        """
        try:
            from docx.shared import Pt, RGBColor
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
        except ImportError:
            return

        tcfg = self.table_cfg
        table.style = tcfg.get("style", "Table Grid")
        header_bold = tcfg.get("header_bold", True)
        header_bg = tcfg.get("header_bg", "")
        header_color = tcfg.get("header_color", "")
        zebra = tcfg.get("zebra", False)
        font_size = tcfg.get("font_size", 10.5)

        for row_idx, row in enumerate(table.rows):
            is_header = row_idx == 0
            zebra_odd = zebra and row_idx % 2 == 1 and not is_header

            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(font_size)
                        if is_header and header_bold:
                            run.bold = True
                        if is_header and header_color:
                            r, g, b = _hex_to_rgb(header_color)
                            run.font.color.rgb = RGBColor(r, g, b)

                # 设置单元格背景色
                if is_header and header_bg:
                    self._set_cell_bg(cell, header_bg)
                elif zebra_odd:
                    self._set_cell_bg(cell, "F5F5F5")

    @staticmethod
    def _set_cell_bg(cell, color_hex: str):
        """设置表格单元格背景色"""
        try:
            from docx.oxml.ns import qn
            from docx.oxml import OxmlElement
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            shd = tcPr.find(qn("w:shd"))
            if shd is None:
                shd = OxmlElement("w:shd")
                tcPr.append(shd)
            shd.set(qn("w:fill"), color_hex.upper().lstrip("#"))
            shd.set(qn("w:val"), "clear")
        except Exception:
            pass

    def get_page_margins_cm(self) -> Dict[str, float]:
        """返回页面边距（cm）"""
        word_cfg = self.output.get("word", {})
        return {
            "top": word_cfg.get("margin_top", 2.54),
            "bottom": word_cfg.get("margin_bottom", 2.54),
            "left": word_cfg.get("margin_left", 3.18),
            "right": word_cfg.get("margin_right", 3.18),
        }

    def should_include_footer(self) -> bool:
        return bool(self.content.get("include_source_footer", True))

    def footer_text(self) -> str:
        return self.content.get("footer_text", "本文档由 AI 整理生成")

    def should_include_date(self) -> bool:
        return bool(self.content.get("include_date", True))

    def should_page_break(self) -> bool:
        return bool(self.content.get("include_page_break", False))


class TemplateEngine:
    """
    模板引擎
    负责发现、加载、校验模板
    """

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = _TEMPLATES_DIR

        self._cache: Dict[str, TemplateConfig] = {}

    def _scan_templates(self) -> List[Path]:
        """扫描所有模板目录（包含 config.yaml 的子目录）"""
        results = []
        if not self.templates_dir.exists():
            return results
        for sub in sorted(self.templates_dir.iterdir()):
            if sub.is_dir() and (sub / "config.yaml").exists():
                results.append(sub)
        return results

    def list_templates(self) -> List[Dict]:
        """
        返回所有可用模板的摘要信息列表
        每项包含: id, name, description, version, path
        """
        summaries = []
        for tpl_dir in self._scan_templates():
            cfg_path = tpl_dir / "config.yaml"
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                tpl_info = raw.get("template", {})
                summaries.append({
                    "id": tpl_info.get("id", tpl_dir.name),
                    "name": tpl_info.get("name", tpl_dir.name),
                    "description": tpl_info.get("description", ""),
                    "version": tpl_info.get("version", "1.0"),
                    "path": str(tpl_dir),
                    "is_user": "user_custom" in str(tpl_dir),
                })
            except Exception as e:
                logger.warning(f"加载模板 {tpl_dir.name} 失败: {e}")

        return summaries

    def load(self, template_id: str = DEFAULT_TEMPLATE_ID) -> TemplateConfig:
        """
        加载指定 ID 的模板配置

        Args:
            template_id: 模板 ID（目录名），如 "default"、"minimalist"

        Returns:
            TemplateConfig 对象

        Raises:
            FileNotFoundError: 模板不存在
        """
        if template_id in self._cache:
            return self._cache[template_id]

        # 精确匹配
        tpl_dir = self.templates_dir / template_id
        if not tpl_dir.exists():
            # 尝试按 name 模糊匹配
            for info in self.list_templates():
                if info["name"] == template_id or info["id"].lower() == template_id.lower():
                    tpl_dir = Path(info["path"])
                    break
            else:
                available = [t["id"] for t in self.list_templates()]
                raise FileNotFoundError(
                    f"模板 '{template_id}' 不存在。可用模板: {available}"
                )

        cfg_path = tpl_dir / "config.yaml"
        with open(cfg_path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        tpl_cfg = TemplateConfig(raw, tpl_dir)
        self._cache[template_id] = tpl_cfg
        logger.info(f"[TEMPLATE] 已加载模板: {tpl_cfg.name} (ID: {tpl_cfg.id})")
        return tpl_cfg

    def load_default(self) -> TemplateConfig:
        """加载默认模板"""
        return self.load(DEFAULT_TEMPLATE_ID)

    def create_user_template(self, template_name: str, base_template: str = DEFAULT_TEMPLATE_ID) -> Path:
        """
        基于现有模板创建用户自定义模板

        Args:
            template_name: 新模板名称（将作为目录名，需符合路径命名规范）
            base_template: 基础模板 ID（复制其 config.yaml 作为起始）

        Returns:
            新模板目录路径
        """
        # 生成安全的目录名
        safe_name = re.sub(r"[^\w\-]", "_", template_name, flags=re.UNICODE)
        new_dir = _USER_TEMPLATES_DIR / safe_name

        if new_dir.exists():
            raise FileExistsError(f"模板 '{safe_name}' 已存在: {new_dir}")

        # 复制基础模板
        base_dir = self.templates_dir / base_template
        if not base_dir.exists():
            raise FileNotFoundError(f"基础模板 '{base_template}' 不存在")

        shutil.copytree(base_dir, new_dir)

        # 更新 config.yaml 中的元信息
        cfg_path = new_dir / "config.yaml"
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg_text = f.read()

        # 替换 id 和 name
        cfg_text = re.sub(r'(id:\s*")[^"]*(")', f'\\g<1>{safe_name}\\2', cfg_text)
        cfg_text = re.sub(r'(name:\s*")[^"]*(")', f'\\g<1>{template_name}\\2', cfg_text)
        cfg_text = re.sub(r'(description:\s*")[^"]*(")',
                          f'\\g<1>用户自定义模板（基于 {base_template}）\\2', cfg_text)

        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(cfg_text)

        logger.info(f"[TEMPLATE] 已创建用户模板: {template_name} -> {new_dir}")
        return new_dir


# ------------------------------------------------------------------ #
# 命令行工具
# ------------------------------------------------------------------ #

def cmd_list():
    """列出所有可用模板"""
    engine = TemplateEngine()
    templates = engine.list_templates()

    if not templates:
        print("未找到可用模板。")
        return

    print("\n" + "=" * 60)
    print(f"可用模板（共 {len(templates)} 个）")
    print("=" * 60)
    for t in templates:
        tag = "[用户自定义]" if t["is_user"] else "[内置]"
        print(f"\n  ID: {t['id']}")
        print(f"  名称: {t['name']} {tag}")
        print(f"  版本: v{t['version']}")
        print(f"  说明: {t['description']}")
        print(f"  路径: {t['path']}")
    print()


def cmd_create(name: str, base: str = DEFAULT_TEMPLATE_ID):
    """创建用户自定义模板"""
    engine = TemplateEngine()
    try:
        new_path = engine.create_user_template(name, base_template=base)
        print(f"\n[OK] 已创建自定义模板: {name}")
        print(f"     路径: {new_path}")
        print(f"     请编辑以下文件来自定义格式:")
        print(f"     {new_path / 'config.yaml'}")
    except FileExistsError as e:
        print(f"[ERROR] {e}")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")


def main():
    import sys
    logging.basicConfig(level=logging.WARNING)

    if len(sys.argv) < 2:
        print("模板引擎 - 命令行工具")
        print("")
        print("用法:")
        print("  python template_engine.py list                           # 列出所有模板")
        print("  python template_engine.py create <名称>                  # 创建自定义模板")
        print("  python template_engine.py create <名称> --base minimalist # 基于极简模板创建")
        return

    command = sys.argv[1]

    if command == "list":
        cmd_list()

    elif command == "create":
        if len(sys.argv) < 3:
            print("[ERROR] 请提供模板名称")
            print("用法: python template_engine.py create <名称>")
            return
        name = sys.argv[2]
        base = DEFAULT_TEMPLATE_ID
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            if args[i] == "--base" and i + 1 < len(args):
                base = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_create(name, base)

    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
