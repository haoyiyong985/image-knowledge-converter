# Tesseract OCR 安装指南

## 📥 下载安装包

### 方式 1：官方推荐（推荐）

1. 访问下载页面：
   ```
   https://digi.bib.uni-mannheim.de/tesseract/
   ```

2. 下载最新版本（选择 64 位）：
   ```
   tesseract-ocr-w64-setup-5.4.0.20240606.exe
   ```
   
   直接下载链接：
   ```
   https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.4.0.20240606.exe
   ```

### 方式 2：备用下载

如果官方下载慢，可以使用国内镜像：
- 清华镜像：https://mirrors.tuna.tsinghua.edu.cn/
- 或百度搜索 "tesseract-ocr-w64-setup 下载"

---

## 🔧 安装步骤

### 步骤 1：运行安装程序

双击下载的 `tesseract-ocr-w64-setup-5.4.0.20240606.exe`

### 步骤 2：选择语言

- 选择 **English**
- 点击 **OK**

### 步骤 3：同意许可协议

- 点击 **I Agree**

### 步骤 4：选择安装路径

- 默认路径：`C:\Program Files\Tesseract-OCR`
- 建议保持默认，点击 **Next**

### 步骤 5：选择组件（★重要★）

**必须勾选以下选项：**

```
☑ Tesseract OCR Engine
☑ Language data (chi_sim)     ← 简体中文，必须勾选！
☑ Language data (chi_tra)     ← 繁体中文（可选）
☑ Language data (eng)         ← 英文（默认已选）
```

![重要] 如果不勾选 chi_sim，将无法识别中文！

### 步骤 6：完成安装

- 点击 **Install** 开始安装
- 等待安装完成
- 点击 **Next** → **Finish**

---

## ⚙️ 配置环境变量

### 方式 1：自动配置（推荐）

运行我创建的批处理脚本：

```bash
D:\新建文件夹\安装Tesseract.bat
```

### 方式 2：手动配置

1. 右键「此电脑」→「属性」
2. 点击「高级系统设置」
3. 点击「环境变量」
4. 在「系统变量」中找到 **Path**
5. 点击「编辑」→「新建」
6. 添加路径：`C:\Program Files\Tesseract-OCR`
7. 点击「确定」保存

---

## 🧪 验证安装

### 测试 1：检查版本

打开新的命令行窗口（必须新开），运行：

```bash
tesseract --version
```

应该显示：
```
tesseract v5.4.0.20240606
 leptonica-1.83.1
  libgif 5.2.1 : libjpeg 8d (libjpeg-turbo 2.1.5) : libpng 1.6.43 : libtiff 4.6.0 : zlib 1.3
```

### 测试 2：检查中文支持

```bash
tesseract --list-langs
```

应该包含：
```
chi_sim
chi_tra
eng
osd
```

### 测试 3：Python 测试

```bash
python -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```

---

## 📦 安装 Python 依赖

```bash
pip install pytesseract pillow
```

---

## ✅ 完成

安装完成后，OCR 管理器会自动检测并使用 Tesseract！

现在您拥有三个 OCR 引擎：
1. **腾讯云 OCR**（首选）
2. **百度 OCR**（第一备用）
3. **本地 Tesseract**（第二备用）

---

## 🆘 常见问题

### Q1: 提示 "tesseract 不是内部或外部命令"

**A**: 环境变量未生效，请：
1. 确认安装路径正确
2. 重新打开命令行窗口
3. 或重启电脑

### Q2: 无法识别中文

**A**: 安装时未勾选 chi_sim 语言包：
1. 重新运行安装程序
2. 选择 "Modify"
3. 勾选 "Chinese (Simplified)"
4. 完成安装

### Q3: Python 提示 "tesseract is not installed"

**A**: 需要安装 pytesseract：
```bash
pip install pytesseract
```

---

**安装完成后，告诉我，我来验证配置！** 🎉
