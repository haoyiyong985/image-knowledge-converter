---
name: image-knowledge-converter
description: 图片截图转知识库工具（V9.5 最新版）。将手机截图自动识别、整理、分类并生成 Markdown/Word 文档，支持 IMA 同步。
version: 1.1.0
tags: [image-processing, knowledge-management, document-generation, ocr]
---

## 功能简介

自动将手机截图（小红书、微信读书、微信等）转化为结构化知识文档。

## 触发词

**中文**：处理新图片、截图转文档、图片知识库、整理截图、初始化知识库  
**英文**：process images、convert screenshots、organize knowledge base

## 安装方式

### 方式一：直接用（推荐）

1. 克隆仓库：
   ```bash
   git clone https://github.com/cuixiaohui985/image-knowledge-converter.git
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行：
   ```bash
   python auto_process_all_v9_4.py
   ```

### 方式二：Skill 导入

1. 下载本 Release 的 `image-knowledge-converter_v1.1.0_skill.zip`
2. 在 WorkBuddy 中导入 Skill
3. 对 WorkBuddy 说 "处理新图片" 即可

## 目录结构

```
image-knowledge-converter/
├── auto_process_all_v9_4.py   ← 主处理脚本（V9.5）
├── requirements.txt
├── ima_config.txt
├── 待处理图片/        ← 放入待处理图片
├── 已处理图片/        ← 处理完后自动归档
└── 处理结果/          ← 生成的 Word/Markdown 文档
```

## 核心功能

- OCR 多引擎：腾讯云 → 百度云 → 本地 Tesseract
- AI 智能分类：动态分类，LLM 自由命名
- 文档合并：同主题自动合并（`{分类}-{主题}` 格式）
- 双格式输出：同时生成 `.docx` 和 `.md`
- IMA 同步：自动同步到 IMA 笔记（可选）

## 版本

**v1.1.0 (2026-04-27)**
- 更新至 V9.5 逻辑
- 删除"综合知识"兜底分类
- 支持 LLM 自由命名分类
- 修复同名文档跨分类误合并

**v1.0.0 (2026-03-17)**
- 初始版本
