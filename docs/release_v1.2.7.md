# GitHub Release v1.2.7 发布内容

## 操作步骤

1. 打开 https://github.com/haoyiyong985/image-knowledge-converter/releases/new
2. 填写以下内容
3. 上传附件 `image-knowledge-converter_v1.2.7_skill_fixed.zip`
4. 点击 Publish release

---

## Tag

```
v1.2.7
```

选择 "Create new tag on publish"，Target 选 `main`

---

## Title

```
v1.2.7 - 13项Bug修复 + 安装向导
```

---

## Description（直接粘贴）

```markdown
## 🔧 核心修复（P0）

- **LLM 配置读取修复**：`_load_config()` 改从 `config['llm']` 子字典读取，修正 key 映射（`kimi_api_key` vs `moonshot_api_key`）— 修复后配置向导设置的 LLM 密钥才能正确生效
- **SKILL.md**：版本号修正为 1.2.7；明确触发词等价关系

## 🔧 配置向导对齐（P1）

- **wizard_processor.py**：支持 `--work-dir` 命名参数（argparse 迁移）
- **setup_wizard.py**：LLM/IMA/SiliconFlow 配置结构与主脚本统一
- **quick_setup.py**：配置结构与 `api_keys.yaml` 对齐
- **api_keys.yaml**：补全 `ima_client_id` 字段
- **混元教程修正**：指向腾讯云 CAM 密钥页，说明混元使用与 OCR 相同密钥

## ✅ 其他改进

- 新增 `.env.template` 模板文件
- `.env` 缺失提示从 WARN 改为 INFO
- 移除 `print_success/print_warn` 重复 emoji
- `config.yaml` 路径改中文目录名，添加说明
- `categories.yaml` 添加 V9.5 动态分类说明
- 混元签名修复（TC3-HMAC-SHA256 + x-tc-action）
- SDK 依赖移除，只需 `requests` 库
- 仓库清理：移除敏感文件和工作空间日志

## 📦 下载

| 文件 | 说明 |
|------|------|
| `image-knowledge-converter_v1.2.7_skill_fixed.zip` | 完整 Skill 包（WorkBuddy 导入即用） |

## 🚀 快速开始

```bash
# 1. 解压到工作目录
# 2. 安装依赖
pip install -r requirements.txt
# 3. 配置 API 密钥（交互式向导）
python setup_wizard.py
# 4. 开始处理
python auto_process_all_v9_4.py
```

---

**完整更新日志**: https://github.com/haoyiyong985/image-knowledge-converter/blob/main/README.md#-更新日志
```

---

## 附件上传

在 Release 页面底部的 "Attach binaries" 区域，拖入：
```
D:\新建文件夹\image-knowledge-converter_v1.2.7_skill_fixed.zip
```
