## 🎉 首次正式发布！

### ✨ 核心功能
- ✅ **OCR 多引擎**：腾讯云 → 百度云 → 本地 Tesseract（自动降级）
- ✅ **AI 智能分类**：动态分类体系，支持自由命名和自动新建分类
- ✅ **文档合并**：同主题内容自动合并到同一文档
- ✅ **双格式输出**：同时生成 .docx 和 .md 文件
- ✅ **IMA 同步**：自动同步到 IMA 笔记（支持增量更新）
- ✅ **分批处理**：大批量图片智能分批，支持断点续传

### 📊 技术指标
- **处理速度**：约 3-5 秒/张（取决于 OCR 引擎）
- **识别准确率**：中文 90%+（腾讯云 OCR）
- **支持格式**：JPG, PNG, WEBP, BMP
- **输出格式**：Word (.docx) + Markdown (.md)

### 📁 项目结构
```
图片知识库转化工具/
├── 待处理图片/              ← 新图片放这里
├── 已处理图片/              ← 处理完的图片自动归档
├── 处理结果/                ← 最终生成的 Word 和 MD 文档
├── auto_process_all_v7.py  ← 主处理脚本
├── ima_sync.py              ← IMA 同步脚本
└── ima_config.txt           ← IMA API 凭证配置
```

### 🚀 使用方法

#### 方式一：作为 WorkBuddy Skill 使用（推荐）
1. 下载本仓库
2. 导入到 WorkBuddy Skills
3. 输入「处理新图片」即可

#### 方式二：本地 Python 运行
```bash
pip install -r requirements.txt
python auto_process_all_v7.py
```

### 📚 文档
- [README.md](README.md) - 完整使用指南
- [使用说明.md](使用说明.md) - 详细操作步骤
- [安装说明.md](安装说明.md) - Skill 安装指南

---

⭐ 如果这个项目对你有帮助，请给它一个星标！

🐛 遇到问题？欢迎提交 [Issue](https://github.com/cuixiaohui985/image-knowledge-converter/issues)！
