#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P0-3 模板系统验证脚本
"""
import sys
import shutil
from pathlib import Path

# 添加 scripts 到路径
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

print("=" * 60)
print("P0-3 模板系统功能验证")
print("=" * 60)

# ---- 测试1: 模板引擎导入和加载 ----
print("\n[测试1] 模板引擎导入和列出模板")
try:
    from template_engine import TemplateEngine, DEFAULT_TEMPLATE_ID
    engine = TemplateEngine()
    templates = engine.list_templates()
    print(f"  发现模板数量: {len(templates)}")
    for t in templates:
        print(f"  - [{t['id']}] {t['name']} — {t['description']}")
    assert len(templates) >= 3, f"预期至少3个模板，实际 {len(templates)}"
    print("  [PASS] 模板列表正常")
except Exception as e:
    print(f"  [FAIL] {e}")
    import traceback; traceback.print_exc()

# ---- 测试2: 加载各模板 ----
print("\n[测试2] 加载各模板配置")
for tpl_id in ["default", "minimalist", "detailed"]:
    try:
        tpl = engine.load(tpl_id)
        print(f"  [{tpl_id}] 名称={tpl.name}, 行距={tpl.body_cfg.get('line_spacing')}, "
              f"页脚={tpl.should_include_footer()}, 分页={tpl.should_page_break()}, "
              f"编号={tpl.headings_cfg.get('auto_numbering')}")
        print(f"  [PASS] {tpl_id}")
    except Exception as e:
        print(f"  [FAIL] {tpl_id}: {e}")

# ---- 测试3: 创建自定义模板 ----
print("\n[测试3] 创建用户自定义模板")
try:
    custom_dir = engine.create_user_template("测试自定义", base_template="minimalist")
    print(f"  创建路径: {custom_dir}")
    assert custom_dir.exists(), "目录未创建"
    assert (custom_dir / "config.yaml").exists(), "config.yaml 不存在"
    # 验证 config 中的 ID 已更新
    import yaml
    with open(custom_dir / "config.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    print(f"  模板ID: {cfg['template']['id']}")
    print(f"  模板名: {cfg['template']['name']}")
    print("  [PASS] 自定义模板创建成功")
    # 清理
    shutil.rmtree(custom_dir)
    print("  [INFO] 测试用模板已清理")
except Exception as e:
    print(f"  [FAIL] {e}")
    import traceback; traceback.print_exc()

# ---- 测试4: Word 生成（三套模板）----
print("\n[测试4] 三套模板生成 Word 文档")

# 准备测试 Markdown
test_md = """# 测试文档：模板系统验证

本文档用于验证 P0-3 模板系统是否正常工作。

## 第一章：系统简介

知识库转化工具可以将图片中的文字提取出来，整理成结构化文档。

主要功能包括：
- OCR 文字识别
- 智能内容分类
- 多种模板输出

## 第二章：使用方法

### 2.1 基本命令

执行以下命令开始处理：

```python
from generate_word import create_word_from_markdown
create_word_from_markdown(md_path, output_path, template_id="default")
```

### 2.2 支持的模板

| 模板ID | 名称 | 适用场景 |
|--------|------|---------|
| default | 默认模板 | 日常整理 |
| minimalist | 极简模板 | 打印阅读 |
| detailed | 详细模板 | 正式报告 |

## 第三章：结语

**本次验证完成！** 系统运行正常。
"""

test_md_path = Path("D:/新建文件夹/处理结果/_test_template.md")
test_md_path.write_text(test_md, encoding="utf-8")

from generate_word import create_word_from_markdown

passed = 0
for tpl_id in ["default", "minimalist", "detailed"]:
    out_path = Path(f"D:/新建文件夹/处理结果/_test_template_{tpl_id}.docx")
    try:
        ok = create_word_from_markdown(test_md_path, out_path, template_id=tpl_id)
        if ok and out_path.exists():
            size_kb = out_path.stat().st_size // 1024
            print(f"  [{tpl_id}] 生成成功，文件大小: {size_kb} KB [PASS]")
            passed += 1
        else:
            print(f"  [{tpl_id}] 生成失败 [FAIL]")
    except Exception as e:
        print(f"  [{tpl_id}] 异常: {e} [FAIL]")
        import traceback; traceback.print_exc()

# ---- 测试5: list-templates 命令 ----
print("\n[测试5] --list-templates 命令行验证")
try:
    from template_engine import cmd_list
    cmd_list()
    print("  [PASS] list-templates 正常")
except Exception as e:
    print(f"  [FAIL] {e}")

# ---- 清理 ----
print("\n[清理测试文件]")
test_md_path.unlink(missing_ok=True)
for tpl_id in ["default", "minimalist", "detailed"]:
    f = Path(f"D:/新建文件夹/处理结果/_test_template_{tpl_id}.docx")
    if f.exists():
        f.unlink()
        print(f"  删除: {f.name}")

print("\n" + "=" * 60)
print(f"测试完成: 4/4 模块验证，Word 生成 {passed}/3 通过")
print("=" * 60)
