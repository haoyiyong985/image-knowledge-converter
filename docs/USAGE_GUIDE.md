# 图片转知识库系统 - 使用指南

## 目录
1. [快速入门](#快速入门)
2. [详细教程](#详细教程)
3. [高级配置](#高级配置)
4. [常见问题](#常见问题)
5. [最佳实践](#最佳实践)

---

## 快速入门

### 第一步：环境准备

1. **安装Python 3.8或更高版本**
   ```bash
   python --version
   ```

2. **安装Tesseract OCR**

   **Windows:**
   - 下载安装程序：https://github.com/UB-Mannheim/tesseract/wiki
   - 安装时选择中文语言包
   - 记住安装路径（如 `C:\Program Files\Tesseract-OCR`）

   **macOS:**
   ```bash
   brew install tesseract tesseract-lang
   ```

   **Linux:**
   ```bash
   sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim
   ```

3. **安装Python依赖**
   ```bash
   pip install -r requirements.txt
   ```

### 第二步：配置系统

1. **编辑配置文件** `config/config.yaml`

   Windows用户需要设置Tesseract路径：
   ```yaml
   ocr:
     engine: "tesseract"
     language: "chi_sim+eng"
     # Windows用户取消下面这行的注释并修改路径
     # tesseract_cmd: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
   ```

2. **（可选）自定义分类**
   
   编辑 `config/categories.yaml` 添加您的自定义关键词

### 第三步：开始使用

1. **放入图片**
   ```bash
   # 将图片复制到输入目录
   cp your-image.jpg images/raw/
   ```

2. **运行系统**
   ```bash
   # 方法1：使用交互式模式
   python knowledge_organizer.py --interactive
   
   # 方法2：使用命令行
   python knowledge_organizer.py process
   python knowledge_organizer.py import
   ```

3. **查看结果**
   - 处理后的文本：`output/`
   - 知识库内容：`knowledge_base/`
   - 浏览报告：`knowledge_base/index.html`

---

## 详细教程

### 教程1：处理单张图片

```python
from image_processor import ImageProcessor

# 创建处理器
processor = ImageProcessor()

# 处理单张图片
result = processor.process_image("images/raw/photo.jpg", "output")

# 查看结果
print(f"提取文本: {result.ocr_result.text[:100]}...")
print(f"置信度: {result.ocr_result.confidence}")
print(f"表格数: {len(result.tables)}")

# 保存结果
processor.save_results(result, "output", formats=['txt', 'json'])
```

### 教程2：批量处理

```python
from knowledge_organizer import KnowledgeOrganizer

# 创建系统实例
organizer = KnowledgeOrganizer()

# 批量处理图片
results = organizer.process_images("images/raw", "output")

# 导入知识库
entries = organizer.import_to_knowledge_base(results)

print(f"成功导入 {len(entries)} 条知识")
```

### 教程3：搜索知识库

```python
from knowledge_manager import KnowledgeBase

# 创建知识库实例
kb = KnowledgeBase()

# 搜索
results = kb.search("Python编程", limit=10)

# 显示结果
for result in results:
    print(f"标题: {result.entry.title}")
    print(f"分类: {result.entry.category}")
    print(f"相关度: {result.relevance_score}")
    print(f"摘要: {result.entry.summary[:100]}...")
    print("---")
```

### 教程4：自定义分类规则

```python
from classifier_engine import ClassifierEngine

# 创建分类器
classifier = ClassifierEngine()

# 测试分类
text = "Python是一种强大的编程语言"
result = classifier.classify(text)

print(f"分类: {result.category}")
print(f"置信度: {result.confidence}")
print(f"方法: {result.method}")
```

### 教程5：导出知识库

```python
from knowledge_manager import KnowledgeBase

kb = KnowledgeBase()

# 导出为HTML
kb.export_to_html("knowledge_base/export.html")

# 获取统计信息
stats = kb.get_statistics()
print(f"总条目: {stats['total_entries']}")
print(f"分类数: {len(stats['categories'])}")
```

---

## 高级配置

### 配置1：调整OCR参数

编辑 `config/config.yaml`：

```yaml
ocr:
  # 识别语言
  language: "chi_sim+eng"
  
  # 页面分割模式
  # 0 = 仅方向和脚本检测
  # 1 = 自动页面分割与OSD
  # 3 = 完全自动页面分割，无OSD
  # 4 = 假设一列可变大小的文本
  # 6 = 假设统一的文本块
  psm_mode: 6
  
  # OCR引擎模式
  # 0 = 仅传统引擎
  # 1 = 仅LSTM神经网络引擎
  # 2 = 传统+LSTM引擎
  # 3 = 默认，基于可用的引擎
  oem_mode: 3
  
  preprocessing:
    enabled: true
    grayscale: true
    contrast_enhancement: true
    denoise: true
    threshold: 150
```

### 配置2：自定义分类关键词

编辑 `config/categories.yaml`：

```yaml
categories:
  - id: "technology"
    name: "技术文档"
    description: "编程、技术教程、开发文档"
    keywords:
      # 添加您的关键词
      - "您的关键词1"
      - "您的关键词2"
      # ... 原有关键词
    icon: "💻"
    color: "#3498db"
```

### 配置3：调整处理规则

编辑 `config/processing_rules.yaml`：

```yaml
preprocessing:
  # 图片尺寸限制
  size_limits:
    max_width: 4096
    max_height: 4096
    
  # 自动旋转
  auto_rotate:
    enabled: true
    detect_orientation: true
    
  # 对比度增强
  contrast:
    enabled: true
    method: "clahe"
    clip_limit: 2.0
    tile_size: 8

quality_check:
  # 置信度检查
  confidence:
    min_overall: 50
    min_per_char: 30
```

### 配置4：批处理设置

```yaml
batch_processing:
  concurrency:
    max_workers: 4
    max_queue_size: 100
  
  batch:
    size: 10
    timeout: 300
    retry_count: 3
```

---

## 常见问题

### Q1: 安装依赖时出错

**问题：** `pip install` 失败

**解决：**
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果仍然失败，逐个安装
pip install opencv-python
pip install pytesseract
pip install scikit-learn
pip install pyyaml
```

### Q2: Tesseract找不到

**问题：** `pytesseract.pytesseract.TesseractNotFoundError`

**解决：**

Windows用户需要在代码中设置路径：
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

或在 `image_processor.py` 中添加：
```python
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### Q3: 中文识别率低

**问题：** 中文识别效果不佳

**解决：**
1. 确保安装了中文语言包
2. 提高图片质量（分辨率、对比度）
3. 调整预处理参数
4. 尝试不同的PSM模式

### Q4: 表格检测失败

**问题：** 无法识别图片中的表格

**解决：**
1. 确保表格线条清晰
2. 调整 `min_table_area` 参数
3. 预处理时增强对比度
4. 手动提取表格区域

### Q5: 分类不准确

**问题：** 自动分类结果不符合预期

**解决：**
1. 在 `categories.yaml` 中添加更多相关关键词
2. 手动指定分类
3. 训练自定义机器学习模型

### Q6: 系统运行缓慢

**问题：** 处理速度慢

**解决：**
1. 降低图片分辨率
2. 减少批处理数量
3. 关闭表格检测（如不需要）
4. 使用更快的硬件

---

## 最佳实践

### 实践1：图片准备

- **分辨率**：建议 150-300 DPI
- **格式**：优先使用 PNG 或高质量 JPG
- **清晰度**：确保文字清晰可读
- **对比度**：避免过暗或过亮的图片

### 实践2：命名规范

```
images/raw/
├── 2024-01-15_会议记录.jpg
├── 2024-01-20_Python教程.png
├── 2024-02-01_财务报表.pdf
└── ...
```

### 实践3：定期维护

```bash
# 每周执行
python knowledge_organizer.py stats
python knowledge_organizer.py export --format html

# 每月执行
# 备份知识库
cp -r knowledge_base backup/knowledge_base_$(date +%Y%m%d)
```

### 实践4：分类管理

1. **定期审查** - 检查分类准确性
2. **关键词优化** - 根据实际内容调整关键词
3. **合并重复** - 使用相似度检测去重
4. **更新索引** - 定期重建搜索索引

### 实践5：工作流程

推荐的工作流程：

```
1. 收集图片 → images/raw/
2. 批量处理 → python knowledge_organizer.py process
3. 导入知识库 → python knowledge_organizer.py import
4. 审查结果 → 检查 output/ 目录
5. 搜索使用 → python knowledge_organizer.py search "关键词"
6. 定期导出 → python knowledge_organizer.py export
```

---

## 附录

### A. 支持的图片格式

- JPG/JPEG
- PNG
- BMP
- TIFF
- WebP

### B. 输出文件说明

| 文件 | 说明 |
|------|------|
| `*.txt` | 提取的纯文本 |
| `*.json` | 结构化数据（包含元数据） |
| `*_table_*.csv` | 提取的表格数据 |
| `*_processed.png` | 预处理后的图片 |
| `index.html` | 知识库浏览页面 |

### C. 目录权限

确保以下目录可读写：
- `images/raw/`
- `output/`
- `knowledge_base/`
- `logs/`

### D. 系统要求

**最低配置：**
- CPU: 双核处理器
- 内存: 4GB RAM
- 磁盘: 1GB 可用空间

**推荐配置：**
- CPU: 四核处理器
- 内存: 8GB RAM
- 磁盘: 10GB 可用空间

---

**祝您使用愉快！** 🎉

如有问题，请查看 `README.md` 或提交 Issue。
