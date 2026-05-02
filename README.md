# 📚 图片知识库转化工具 (Image Knowledge Converter)

> 自动将手机截图转换为结构化 Word + Markdown 知识文档，并同步到 IMA 个人笔记

[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cuixiaohui985/image-knowledge-converter?style=social)](https://github.com/cuixiaohui985/image-knowledge-converter)
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-Skill-green)](https://workbuddy.ai)

---

## 🌟 项目简介

**图片知识库转化工具** 是一个智能知识管理助手，能够：

- 📷 **自动识别**：从手机截图（小红书、微信读书、微信等）中提取文字
- 🏷️ **智能分类**：AI 理解内容并自动分类到对应知识主题
- 📝 **生成文档**：输出结构化 Word + Markdown 双格式文档
- 🔗 **自动归档**：按分类整理图片和文档
- 🔄 **内容合并**：相似主题自动合并，避免重复
- ☁️ **云端同步**：一键同步到 IMA 个人笔记

---

## ✨ 功能特点

### 核心功能

| 功能 | 说明 |
|------|------|
| **OCR 多引擎** | 腾讯云 → 百度云 → 本地 Tesseract（自动降级） |
| **AI 智能分类** | 动态分类体系，支持自由命名和自动新建分类 |
| **文档合并** | 同主题内容自动合并到同一文档 |
| **双格式输出** | 同时生成 `.docx` 和 `.md` 文件 |
| **IMA 同步** | 自动同步到 IMA 笔记（支持增量更新）|
| **分批处理** | 大批量图片智能分批，支持断点续传 |
| **重复检测** | Hash + 主题词相似度双重检测 |

### 技术亮点

- ✅ **LLM 全覆盖**：混元 Lite / Kimi / Doubao 多模型兜底
- ✅ **智能命名**：`{分类}-{主题}`，如 `历史文化-钱谦益传`
- ✅ **内容整理**：自动修复 OCR 错误、结构化排版
- ✅ **来源提取**：自动识别小红书、微信等平台来源

---

## 🚀 快速开始

### 方式一：WorkBuddy Skill（推荐）

1. **下载 Skill**
   ```bash
   # 克隆仓库
   git clone https://github.com/cuixiaohui985/image-knowledge-converter.git
   ```

2. **导入到 WorkBuddy**
   - 打开 WorkBuddy → 点击右上角头像 → **Skills 管理**
   - 点击「导入 Skills」
   - 选择 `dist/image-knowledge-converter_*.zip`
   - 点击「立即导入」

3. **初始化知识库**
   在 WorkBuddy 中输入：
   ```
   初始化知识库
   ```

4. **放入图片并开始处理**
   ```
   处理新图片
   ```

---

### 方式二：本地 Python 运行

#### 环境要求

- Python 3.8+
- Tesseract OCR（可选，用于本地兜底）

#### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/cuixiaohui985/image-knowledge-converter.git
   cd image-knowledge-converter
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 OCR（可选）**
   - 腾讯云 OCR：配置 `ocr_config.json`
   - 百度云 OCR：配置 `ocr_config.json`
   - 本地 Tesseract：安装后自动调用

4. **运行处理**
   ```bash
   python auto_process_all_v7.py
   ```

---

## 📖 使用指南

### 目录结构

```
D:\新建文件夹\
├── 待处理图片\              ← 新图片放这里（按主题分子文件夹）
│   ├── 健康养生\
│   ├── 旅行记录\
│   └── ...
├── 已处理图片\              ← 处理完的图片自动归档
├── 处理结果\                ← 最终生成的 Word 和 MD 文档
│   ├── 历史文化-钱谦益传.docx
│   ├── 历史文化-钱谦益传.md
│   └── ...
├── auto_process_all_v7.py  ← 主处理脚本
├── ima_sync.py              ← IMA 同步脚本
└── ima_config.txt           ← IMA API 凭证配置
```

### 日常使用流程

#### 第 1 步：放入新图片
把手机截图复制到对应主题文件夹：
```
待处理图片\健康养生\  ← 健康类图片
待处理图片\旅行记录\  ← 旅行类图片
```

#### 第 2 步：打开 WorkBuddy，恢复背景
> ⚠️ **重要**：WorkBuddy 每次新开对话都是"空白"状态，必须先粘贴启动提示词。

1. 打开 `【启动提示词】新对话粘贴这段.txt`
2. 全选内容（Ctrl+A），复制（Ctrl+C）
3. 粘贴到 WorkBuddy 对话框，发送

#### 第 3 步：发送指令，开始处理
```
处理新图片
```

AI 会自动完成：
1. 读取已有文档的章节结构
2. 逐张识别图片中的文字
3. 判断内容属于哪个分类
4. 同类内容 → 追加到已有文档
5. 新主题内容 → 自动新建文档
6. 处理完的图片移动到 `已处理图片\`

---

## ⚙️ 配置说明

### IMA 同步配置（可选）

1. 打开 `ima_config.txt`
2. 填入你的 Client ID 和 API Key：
   ```
   IMA_CLIENT_ID=你的ClientID
   IMA_API_KEY=你的APIKey
   ```
3. 保存文件

> 凭证获取地址：https://ima.qq.com/agent-interface

### OCR 配置（可选）

编辑 `ocr_config.json`：
```json
{
  "tencent": {
    "secret_id": "你的腾讯云SecretId",
    "secret_key": "你的腾讯云SecretKey"
  },
  "baidu": {
    "api_key": "你的百度API Key",
    "secret_key": "你的百度Secret Key"
  }
}
```

---

## 📊 分类体系

### 预设分类（可自动扩展）

| 分类 | 说明 | 示例 |
|------|------|------|
| **历史文化** | 历史、人物传记、文化知识 | 钱谦益传、南宋历史 |
| **营养健康** | 饮食、营养、健康知识 | 抗炎饮食、肠道健康 |
| **生活方式** | 运动、睡眠、日常建议 | 日常饮食建议 |
| **教育育儿** | 教育方法、育儿知识 | - |
| **旅游攻略** | 旅行记录、景点介绍 | - |

### 动态分类

当内容不属于预设分类时，AI 会：
1. 自动判断新主题名称
2. 自由命名分类
3. 创建新分类并归档

---

## 💡 常用指令

在 WorkBuddy 对话中可以使用：

| 指令 | 效果 |
|------|------|
| `处理新图片` | 处理所有待处理图片 |
| `处理待处理图片/健康养生` | 只处理指定文件夹的图片 |
| `查看现有文档` | 列出所有文档和章节列表 |
| `工具优化` | 优化工具性能和功能 |

---

## 📂 输出示例

### 处理结果目录

```
处理结果\
├── 历史文化-钱谦益传.docx
├── 历史文化-钱谦益传.md
├── 历史文化-南宋历史概述.docx
├── 历史文化-南宋历史概述.md
└── ...
```

### 文档内容结构

```markdown
# 历史文化-钱谦益传

## 一、生平简介
（OCR 识别内容，AI 自动分段）

## 二、主要成就
（结构化整理）

## 三、历史评价
（自动分类归档）
```

---

## 🔧 高级功能

### 分批处理

处理大量图片时，系统会自动分批：

| 图片大小 | 每批数量 |
|---------|---------|
| < 500KB | 10 张/批 |
| 500KB-2MB | 6 张/批 |
| 2MB-5MB | 4 张/批 |
| > 5MB | 2 张/批 |

### 断点续传

如果处理中断，可以恢复：
```bash
python auto_process_all_v6.py --batch
```

查看进度：
```bash
python auto_process_all_v6.py --progress
```

清除状态：
```bash
python auto_process_all_v6.py --clear
```

---

## 🐛 常见问题

### Q1：OCR 识别失败怎么办？

**解决**：
1. 检查图片清晰度（建议分辨率 ≥ 150 DPI）
2. 确认已配置腾讯云/百度云 OCR
3. 安装本地 Tesseract 作为兜底

### Q2：文档命名不符合预期？

**解决**：
- 文档命名格式：`{分类}-{主题}`
- 如需自定义，可修改 `auto_process_all_v7.py` 中的命名规则

### Q3：如何避免重复内容？

**解决**：
- 系统自动检测重复（Hash + 主题词相似度）
- 重复图片会自动跳过

### Q4：IMA 同步失败？

**解决**：
1. 检查 `ima_config.txt` 配置是否正确
2. 确认凭证未过期
3. 运行 `python ima_sync.py --check` 验证凭证

---

## 📈 性能指标

- **处理速度**：约 3-5 秒/张（取决于 OCR 引擎）
- **识别准确率**：中文 90%+（腾讯云 OCR）
- **支持格式**：JPG, PNG, WEBP, BMP
- **输出格式**：Word (.docx) + Markdown (.md)

---

## 🛠️ 技术栈

| 技术 | 用途 |
|------|------|
| **OCR** | 腾讯云、百度云、Tesseract |
| **AI 分析** | 混元 Lite、Kimi、Doubao |
| **文档生成** | python-docx |
| **同步** | IMA OpenAPI |
| **语言** | Python 3.8+ |

---

## 📄 文件说明

### 核心脚本

| 文件 | 说明 |
|------|------|
| `auto_process_all_v7.py` | 当前最新版本（V9.5 逻辑） |
| `auto_process_all_v6.py` | 分批处理版本 |
| `ima_sync.py` | IMA 同步脚本 |
| `classifier_engine.py` | 分类引擎 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `ocr_config.json` | OCR 凭证配置 |
| `ima_config.txt` | IMA API 凭证 |
| `.env` | 环境变量（不提交到 Git） |

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 📝 更新日志

### v1.0 (2026-03-17)
- ✅ 初始版本发布
- ✅ 支持 OCR 识别（腾讯云、百度云、Tesseract）
- ✅ AI 智能分类和文档合并
- ✅ Word + Markdown 双格式输出
- ✅ IMA 同步功能

### v2.0 (2026-04-07)
- ✅ 分批处理支持
- ✅ 断点续传
- ✅ 动态分类体系

### v3.0 (2026-04-27)
- ✅ LLM 多模型兜底
- ✅ 删除"综合知识"分类
- ✅ 自由命名分类

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [WorkBuddy](https://workbuddy.ai) - AI 助手平台
- [腾讯云 OCR](https://cloud.tencent.com/product/ocr) - OCR 服务
- [百度云 OCR](https://ai.baidu.com/tech/ocr) - OCR 服务
- [Tesseract](https://github.com/tesseract-ocr/tesseract) - 开源 OCR 引擎

---

## � contact

- GitHub Issues：[提交问题](https://github.com/cuixiaohui985/image-knowledge-converter/issues)
- 邮箱：（添加你的联系方式）

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！**
