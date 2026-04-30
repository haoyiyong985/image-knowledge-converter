#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全自动化图片处理工具 V4.0
==============================
修复问题（V4.0）：
  1. 分类归档：按主题分类到对应的子文件夹
  2. 文件命名：根据图片内容提取有意义标题，无内容时用源文件夹名
  3. 内容合并：同一主题的内容合并到同一文档
  4. 文档内容：确保OCR内容完整生成
  5. 归档结构：按主题分类归档到对应子文件夹
  6. 进度显示：实时显示处理状态

使用方法：
  python auto_process_all_v4.py
"""

import os
import sys
import io
import json
import time
import re
import hashlib
import shutil
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional, List, Dict

# 修复 Windows 控制台编码
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# 添加项目根目录到路径
sys.path.insert(0, '.')

# 加载 .env 环境变量配置
from dotenv import load_dotenv
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    print("[WARN] .env 文件不存在，使用系统环境变量")

# 导入各模块
from local_ocr import LocalOCR
from scripts.classifier_engine import ClassifierEngine

# 尝试导入云端OCR
try:
    from tencent_ocr import TencentOCR
    TENINCENT_AVAILABLE = True
except ImportError:
    TENINCENT_AVAILABLE = False

try:
    from baidu_ocr import BaiduOCR
    BAIDU_AVAILABLE = True
except ImportError:
    BAIDU_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('处理结果/process.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# 主题分类配置
# ============================================================
THEME_KEYWORDS = {
    "中医养生": ["中医", "养生", "药膳", "食疗", "中药", "经络", "穴位", "调理", "体质", "气血", "肝", "肾", "脾", "胃", "湿气", "虚", "寒", "热", "上火", "补", "滋阴", "温阳", "祛湿", "健脾", "润肺", "养心", "补肾", "中医师", "中医说", "中医认为"],
    "健康饮食": ["饮食", "营养", "食物", "蔬菜", "水果", "蛋白质", "碳水", "健康", "抗炎", "抗氧化", "免疫力", "肠道", "益生元", "膳食纤维", "维生素", "矿物质", "有机", "纯天然", "少油", "少盐", "清淡", "养生餐", "健康餐"],
    "疾病防治": ["疾病", "预防", "治疗", "症状", "指标", "血压", "血糖", "血脂", "胆固醇", "尿酸", "脂肪肝", "结节", "囊肿", "肿瘤", "癌症", "慢性病", "并发症", "吃药", "服药", "手术", "复查", "就医", "医院", "医生", "确诊"],
    "生活方式": ["运动", "睡眠", "压力", "情绪", "心理健康", "作息", "习惯", "减肥", "增重", "美容", "护肤", "跑步", "走路", "瑜伽", "冥想", "放松", "健身", "锻炼"],
    "营养科普": ["科普", "知识", "研究", "发现", "实验", "数据", "结论", "专家", "建议", "指南", "推荐", "科学", "原理", "机制", "分析", "解读", "揭秘", "真相", "为什么", "是什么"],
    "育儿教育": ["育儿", "宝宝", "孩子", "教育", "辅食", "喂养", "早教", "亲子", "成长", "发育", "妈妈", "孕妇", "备孕", "新生儿", "婴儿", "幼儿", "儿童"],
    "美食烹饪": ["美食", "烹饪", "做法", "菜谱", "食谱", "食材", "配料", "做饭", "煮", "炒", "炖", "蒸", "烤", "炸", "凉拌", "汤", "粥", "面食", "烘焙", "蛋糕", "面包"]
}


# ============================================================
# 进度条显示
# ============================================================
class ProgressBar:
    """终端进度条"""
    
    def __init__(self, total: int, width: int = 40, prefix: str = "进度"):
        self.total = total
        self.width = width
        self.prefix = prefix
        self.current = 0
        self.start_time = time.time()
        
    def update(self, current: int, info: str = ""):
        self.current = current
        percent = current / self.total if self.total > 0 else 0
        filled = int(self.width * percent)
        bar = '█' * filled + '░' * (self.width - filled)
        
        # 计算ETA
        if current > 0:
            elapsed = time.time() - self.start_time
            eta = elapsed / current * (self.total - current)
            if eta > 60:
                eta_str = f"{int(eta/60)}分{int(eta%60)}秒"
            else:
                eta_str = f"{int(eta)}秒"
        else:
            eta_str = "--"
            
        print(f"\r{self.prefix}: |{bar}| {current}/{self.total} ({percent:.0%}) ETA:{eta_str} {info[:15]}", 
              end='', flush=True)
        
    def finish(self):
        self.current = self.total
        self.update(self.total, "完成!")
        print()


# ============================================================
# 图片归档器 - 按主题分类归档
# ============================================================
class ImageArchiver:
    """图片归档器 - 处理完成后按主题分类移动图片"""
    
    def __init__(self, processed_dir: str = '已处理图片'):
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.archived_count = 0
        
    def archive_image(self, image_path: str, theme: str = None) -> Optional[str]:
        """移动图片到按主题分类的已处理文件夹"""
        src = Path(image_path)
        if not src.exists():
            return None
            
        # 确定归档的目标子文件夹
        if theme and theme in THEME_KEYWORDS:
            archive_subdir = self.processed_dir / theme
        else:
            # 使用源文件夹名作为子文件夹名
            source_folder = src.parent.name
            if source_folder and source_folder not in ['待处理图片', 'images', 'source']:
                archive_subdir = self.processed_dir / source_folder
            else:
                archive_subdir = self.processed_dir / "其他"
        
        archive_subdir.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名（避免覆盖）
        dest_name = src.name
        dest = archive_subdir / dest_name
        
        if dest.exists():
            # 文件已存在，添加时间戳
            timestamp = datetime.now().strftime('%H%M%S')
            name_parts = src.stem, src.suffix
            dest = archive_subdir / f"{name_parts[0]}_{timestamp}{name_parts[1]}"
        
        try:
            # 移动文件
            shutil.move(str(src), str(dest))
            self.archived_count += 1
            return str(dest)
        except Exception as e:
            logger.warning(f"[归档] 移动失败 {src.name}: {e}")
            # 尝试复制
            try:
                shutil.copy2(str(src), str(dest))
                src.unlink()  # 删除原文件
                self.archived_count += 1
                return str(dest)
            except:
                return None
                
    def get_archive_stats(self) -> Dict:
        """获取归档统计"""
        total = 0
        subdirs = {}
        for item in self.processed_dir.iterdir():
            if item.is_dir():
                count = len(list(item.glob('*.*')))
                subdirs[item.name] = count
                total += count
        return {
            'archived_count': self.archived_count,
            'total_archived': total,
            'subdirs': subdirs
        }


# ============================================================
# 内容整理器
# ============================================================
class ContentOrganizer:
    """内容整理器 - 对OCR识别的原始内容进行智能整理"""

    def __init__(self):
        self.source_keywords = ['来源', '出处', '作者', '小红书', '微信', '抖音', '微博', 'B站', '公众号']
        
        # 段落分隔关键词
        self.section_keywords = [
            '一、', '二、', '三、', '四、', '五、', '六、',
            '1.', '2.', '3.', '4.', '5.', '6.',
            '（1）', '（2）', '（3）', '（4）',
            '第一', '第二', '第三', '第四', '第五',
            '首先', '其次', '然后', '最后', '另外', '此外'
        ]

    def clean_text(self, text: str) -> str:
        """清理OCR识别的原始文本"""
        lines = text.split('\n')
        cleaned_lines = []
        prev_line_empty = False

        for line in lines:
            line = line.strip()

            if len(line) < 2 and line:
                continue

            # 跳过纯分隔线
            if re.match(r'^[_\-=]{3,}$', line):
                continue

            # 跳过纯英文行（太长）
            if re.match(r'^[a-zA-Z0-9\s]{20,}$', line) and not re.search(r'[\u4e00-\u9fa5]', line):
                continue

            # 跳过UI元素行
            ui_patterns = ['开始', '插入', '绘图', '设计', '切换', '动画', '审阅', '视图', '帮助', '文件', '编辑', '格式', '工具', '表格']
            if any(ui in line for ui in ui_patterns) and len(line) < 10:
                continue

            if not line:
                if not prev_line_empty:
                    cleaned_lines.append('')
                    prev_line_empty = True
                continue

            prev_line_empty = False
            line = self._fix_common_ocr_errors(line)
            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        return result.strip()

    def _fix_common_ocr_errors(self, line: str) -> str:
        """修复常见的OCR错误"""
        replacements = [
            (chr(8220), '"'), (chr(8221), '"'),
            (chr(8216), "'"), (chr(8217), "'"), (chr(8218), "'"),
            (chr(8222), '"'), (chr(8223), '"'),
            (chr(8242), "'"), (chr(8243), "'"),
            (chr(180), ""), (chr(9032), ""),
            (chr(8212), "-"), (chr(183), "-"),
            ('`', ''), ('√', '✓'), ('×', '✗')
        ]
        for old, new in replacements:
            line = line.replace(old, new)
        line = re.sub(r' {2,}', ' ', line)
        return line

    def structure_content(self, text: str) -> str:
        """对内容进行智能结构化处理"""
        lines = text.split('\n')
        structured = []
        current_h2 = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测是否为二级标题
            is_heading = False
            if re.match(r'^[一二三四五六七八九十百千零\d]+[、.．:：]', line) and len(line) <= 25:
                structured.append(f"### {line}")
                current_h2 = line
                is_heading = True
            elif line.startswith('**') and line.endswith('**') and len(line) <= 30:
                structured.append(f"### {line.strip('*')}")
                current_h2 = line
                is_heading = True
            elif any(line.startswith(kw) for kw in self.section_keywords) and len(line) <= 40:
                structured.append(f"### {line}")
                current_h2 = line
                is_heading = True
            elif re.match(r'^[\u4e00-\u9fa5]{4,15}$', line) and len(line) <= 20:
                # 短纯中文行，可能是标题
                if not re.search(r'[a-zA-Z0-9]', line):
                    structured.append(f"## {line}")
                    continue

            if not is_heading:
                structured.append(line)

        return '\n'.join(structured)


# ============================================================
# 文档生成器 - 同一主题合并到同一文档
# ============================================================
class DocumentGenerator:
    """文档生成器 - 同一主题合并到同一文档"""

    def __init__(self, output_dir: str = '处理结果'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.theme_docs = {}  # {theme: {doc_name: {'file': Path, 'count': int}}}
        self.generated_hashes = set()
        self._scan_existing_docs()

    def _scan_existing_docs(self):
        """扫描现有文档"""
        for theme_folder in self.output_dir.iterdir():
            if theme_folder.is_dir() and not theme_folder.name.startswith('.'):
                for md_file in theme_folder.glob('*.md'):
                    theme = theme_folder.name
                    doc_name = md_file.stem
                    if theme not in self.theme_docs:
                        self.theme_docs[theme] = {}
                    self.theme_docs[theme][doc_name] = {
                        'file': md_file,
                        'count': 0
                    }
                    # 读取hash
                    try:
                        content = md_file.read_text(encoding='utf-8')
                        hash_match = re.search(r'content_hash:\s*([a-f0-9]{8})', content)
                        if hash_match:
                            self.generated_hashes.add(hash_match.group(1))
                    except:
                        pass

    def is_duplicate(self, content_hash: str) -> bool:
        """检查内容是否重复"""
        return content_hash in self.generated_hashes

    def _generate_doc_name(self, text: str, theme: str, source_folder: str = None) -> str:
        """生成文档名：优先使用图片所在文件夹名，其次使用内容关键词"""
        
        # 如果有源文件夹名，优先使用
        if source_folder and source_folder not in ['待处理图片', 'images', 'source', 'images']:
            # 清理文件夹名
            name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', source_folder)
            if len(name) >= 2:
                return name

        # 从内容中提取标题
        lines = text.split('\n')[:20]
        
        # 查找Markdown标题
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                title = line.lstrip('#').strip()
                if 2 <= len(title) <= 20:
                    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title)
            if re.match(r'^[\u4e00-\u9fa5]{4,15}$', line) and len(line) <= 20:
                if not re.search(r'[a-zA-Z0-9]', line):
                    return line
        
        # 查找关键词组合
        title_keywords = ['知识', '指南', '攻略', '技巧', '方法', '注意', '禁忌', '功效', '作用', '食谱', '方子']
        for line in lines:
            line = line.strip()
            for kw in title_keywords:
                if kw in line and 4 <= len(line) <= 20:
                    return re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', line)
        
        # 使用主题名
        return f"{theme}_整理"

    def generate_document(self, text: str, theme: str, image_name: str, 
                          content_hash: str = None, source_folder: str = None) -> str:
        """生成或追加到文档（同一主题合并）"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # 确保主题文件夹存在
        theme_folder = self.output_dir / theme
        theme_folder.mkdir(exist_ok=True)
        
        # 生成文档名
        doc_name = self._generate_doc_name(text, theme, source_folder)
        
        # 检查该主题下是否有同名文档
        if theme not in self.theme_docs:
            self.theme_docs[theme] = {}
        
        if doc_name in self.theme_docs[theme]:
            # 追加到现有文档
            existing_file = self.theme_docs[theme][doc_name]['file']
            self._append_to_document(existing_file, text, image_name, content_hash, timestamp)
            self.theme_docs[theme][doc_name]['count'] += 1
            logger.info(f"[文档] 追加到: {theme}/{doc_name}.md")
            return str(existing_file)
        else:
            # 创建新文档
            new_file = self._create_new_document(
                theme_folder, doc_name, text, theme, image_name, 
                content_hash, timestamp
            )
            self.theme_docs[theme][doc_name] = {
                'file': new_file,
                'count': 1
            }
            if content_hash:
                self.generated_hashes.add(content_hash)
            logger.info(f"[文档] 新建: {theme}/{doc_name}.md")
            return str(new_file)

    def _create_new_document(self, theme_folder: Path, doc_name: str, text: str,
                            theme: str, image_name: str, content_hash: str, timestamp: str) -> Path:
        """创建新文档"""
        # 清理文档名
        safe_name = re.sub(r'[<>:"/\|?*]', '', doc_name)
        if len(safe_name) > 25:
            safe_name = safe_name[:25]
        
        md_file = theme_folder / f"{safe_name}.md"
        counter = 1
        while md_file.exists():
            md_file = theme_folder / f"{safe_name}_{counter}.md"
            counter += 1

        # 整理内容
        organizer = ContentOrganizer()
        cleaned_text = organizer.clean_text(text)
        structured_text = organizer.structure_content(cleaned_text)

        content = f"""# {doc_name}

> 来源图片: {image_name}
> 识别时间: {timestamp}
> 主题分类: {theme}
> content_hash: {content_hash or 'N/A'}

---

{structured_text}

---

*本文档由图片知识库整理工具自动生成*
"""
        
        md_file.write_text(content, encoding='utf-8')
        return md_file

    def _append_to_document(self, existing_file: Path, new_text: str, 
                           image_name: str, content_hash: str, timestamp: str):
        """追加内容到现有文档"""
        try:
            existing_content = existing_file.read_text(encoding='utf-8')
            
            # 整理新内容
            organizer = ContentOrganizer()
            cleaned_text = organizer.clean_text(new_text)
            structured_text = organizer.structure_content(cleaned_text)
            
            # 创建追加内容
            append_section = f"""

---

## 📌 补充内容

> 来源图片: {image_name}
> 追加时间: {timestamp}

{structured_text}

"""
            
            # 在结尾标记前插入
            if existing_content.endswith('*本文档由图片知识库整理工具自动生成*'):
                new_content = existing_content.replace(
                    '\n\n---\n\n*本文档由图片知识库整理工具自动生成*',
                    append_section + '\n\n---\n\n*本文档由图片知识库整理工具自动生成*'
                )
            else:
                new_content = existing_content + append_section
            
            existing_file.write_text(new_content, encoding='utf-8')
            
            if content_hash:
                self.generated_hashes.add(content_hash)
                
        except Exception as e:
            logger.warning(f"[追加] 失败: {e}")


# ============================================================
# 主题分类器
# ============================================================
class ThemeClassifier:
    """主题分类器 - 根据内容分类"""

    def classify(self, text: str) -> str:
        """分类文本到主题"""
        scores = {}
        
        for theme, keywords in THEME_KEYWORDS.items():
            score = 0
            for kw in keywords:
                if kw in text:
                    score += 1
            if score > 0:
                scores[theme] = score
        
        if scores:
            # 返回得分最高的主题
            best_theme = max(scores, key=scores.get)
            if scores[best_theme] >= 1:
                return best_theme
        
        return "综合知识"


# ============================================================
# 多引擎OCR
# ============================================================
class MultiEngineOCR:
    """多引擎OCR管理器"""

    def __init__(self):
        self.current_engine = None
        self.engine_status = []

        secret_id = os.getenv('TENCENT_SECRET_ID', '')
        secret_key = os.getenv('TENCENT_SECRET_KEY', '')
        if secret_id and secret_key and '替换' not in secret_id and TENINCENT_AVAILABLE:
            self.engine_status.append(('腾讯云', True, '已配置'))
        else:
            self.engine_status.append(('腾讯云', False, '未配置'))

        app_id = os.getenv('BAIDU_APP_ID', '')
        api_key = os.getenv('BAIDU_API_KEY', '')
        secret_key = os.getenv('BAIDU_SECRET_KEY', '')
        if app_id and api_key and secret_key and '替换' not in app_id and BAIDU_AVAILABLE:
            self.engine_status.append(('百度云', True, '已配置'))
        else:
            self.engine_status.append(('百度云', False, '未配置'))

        local = LocalOCR()
        if local.tesseract_available:
            self.engine_status.append(('本地Tesseract', True, '可用'))
        else:
            self.engine_status.append(('本地Tesseract', False, getattr(local, 'error_message', '未知错误')))

        self._select_best_engine()

    def _select_best_engine(self):
        for name, available, msg in self.engine_status:
            if available:
                self.current_engine = name
                logger.info(f"[OCR] 选用引擎: {name} ({msg})")
                return True
        logger.warning("[OCR] 没有可用的OCR引擎!")
        return False

    def recognize(self, image_path: str, timeout: int = 60) -> Dict:
        """识别图片文字"""
        last_error = None
        for name, available, _ in self.engine_status:
            if not available:
                continue
            try:
                logger.info(f"[OCR] 尝试 {name}...")
                if name == '腾讯云' and TENINCENT_AVAILABLE:
                    engine = TencentOCR()
                elif name == '百度云' and BAIDU_AVAILABLE:
                    engine = BaiduOCR()
                else:
                    engine = LocalOCR()

                result = engine.recognize(image_path)
                if result and result.get('success'):
                    logger.info(f"[OCR] {name} 识别成功!")
                    return result
                else:
                    last_error = result.get('error', '未知错误') if result else '返回为空'
            except Exception as e:
                last_error = str(e)
        return {'success': False, 'error': last_error or '无可用OCR引擎', 'text': ''}


# ============================================================
# IMA同步器
# ============================================================
class IMASyncer:
    """IMA笔记同步器"""

    def __init__(self):
        self.client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
        self.api_key = os.getenv('IMA_OPENAPI_APIKEY', '')
        self.base_url = 'https://ima.qq.com/openapi/note/v1'
        self.enabled = bool(self.client_id and self.api_key and '填入' not in self.client_id)
        self.sync_log_file = Path('处理结果/ima_sync_log.json')
        self.sync_log = self._load_sync_log()
        self.rate_limited = False

        if self.enabled:
            logger.info("[IMA] 已配置")
        else:
            logger.warning("[IMA] 未配置")

    def _load_sync_log(self) -> Dict:
        if self.sync_log_file.exists():
            try:
                return json.loads(self.sync_log_file.read_text(encoding='utf-8'))
            except:
                pass
        return {}

    def sync_note(self, title: str, content: str, theme: str = None, 
                  content_hash: str = None) -> Optional[str]:
        if not self.enabled or self.rate_limited:
            return None

        doc_key = content_hash or title
        existing = self.sync_log.get(doc_key, {})

        full_content = f"# {title}\n\n"
        if theme:
            full_content += f"> 主题: {theme}\n"
        if content_hash:
            full_content += f"> 内容标识: {content_hash}\n"
        full_content += f"\n{content}\n\n---\n*自动同步自图片知识库*\n"

        result = self._api_call('import_doc', {
            'content_format': 1,
            'content': full_content
        })

        if result and result.get('code') == 0:
            doc_id = result.get('data', {}).get('note_id', '')
            if doc_id:
                self.sync_log[doc_key] = {
                    'doc_id': doc_id,
                    'first_sync': datetime.now().isoformat(),
                    'last_sync': datetime.now().isoformat(),
                    'theme': theme
                }
                self._save_sync_log()
                logger.info(f"[IMA] 笔记已同步: {title[:20]}")
                return doc_id
            else:
                return "imported"
        return None

    def _api_call(self, endpoint: str, payload: Dict, retries: int = 3) -> Optional[Dict]:
        if not self.enabled or self.rate_limited:
            return None

        for attempt in range(retries):
            try:
                import requests
                headers = {
                    'ima-openapi-clientid': self.client_id,
                    'ima-openapi-apikey': self.api_key,
                    'Content-Type': 'application/json'
                }
                url = f"{self.base_url}/{endpoint}"
                response = requests.post(url, json=payload, headers=headers, timeout=30)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 403:
                    result = response.json()
                    if '请求超量' in result.get('msg', ''):
                        logger.warning("[IMA] API请求超量，已触发限流")
                        self.rate_limited = True
                        return None
                return None
            except Exception as e:
                logger.warning(f"[IMA] API调用失败 ({attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(2)
        return None

    def _save_sync_log(self):
        self.sync_log_file.write_text(
            json.dumps(self.sync_log, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )


# ============================================================
# 主处理函数
# ============================================================
def process_single_image(ocr, classifier, doc_gen, ima_syncer, archiver,
                         image_path: str, index: int, total: int, 
                         progress: ProgressBar = None):
    """处理单张图片"""
    image_name = Path(image_path).name
    source_folder = Path(image_path).parent.name  # 获取源文件夹名
    
    # 更新进度条
    if progress:
        progress.update(index, f"[{index}/{total}]")
    
    print(f"\n{'='*50}")
    print(f"[{index}/{total}] 处理: {image_name}")
    print(f"  📁 源文件夹: {source_folder}")
    print(f"{'='*50}")

    # 1. OCR识别
    print("\n📷 OCR识别中...")
    start_time = time.time()
    result = ocr.recognize(image_path)
    ocr_time = time.time() - start_time

    if not result.get('success'):
        print(f"  ⚠️ OCR失败: {result.get('error')}")
        archiver.archive_image(image_path)  # 归档失败图片
        return None

    text = result.get('text', '').strip()
    if not text or len(text) < 10:
        print("  ⚠️ 无文字内容或内容过少")
        archiver.archive_image(image_path)
        return None

    print(f"  ✓ 识别到 {len(text)} 个字符 (耗时 {ocr_time:.1f}秒)")

    # 2. 主题分类
    print("\n🏷️ 主题分类中...")
    theme = classifier.classify(text)
    print(f"  ✓ 分类: {theme}")

    # 3. 计算内容哈希
    content_hash = hashlib.md5(text[:500].encode('utf-8')).hexdigest()[:8]
    
    # 4. 检测重复
    print("\n🔍 检测重复...")
    if doc_gen.is_duplicate(content_hash):
        print("  ⚠️ 检测到重复内容，跳过存储")
        archiver.archive_image(image_path, theme)
        return {
            'image': image_name,
            'text_length': len(text),
            'theme': theme,
            'is_duplicate': True,
            'content_hash': content_hash
        }
    print("  ✓ 新内容")

    # 5. 生成文档（同一主题合并）
    print("\n📝 生成文档中...")
    doc_file = doc_gen.generate_document(
        text, theme, image_name, content_hash, source_folder
    )
    if doc_file:
        rel_path = Path(doc_file).relative_to(doc_gen.output_dir)
        print(f"  ✓ 已保存: {rel_path}")

    # 6. IMA同步
    print("\n☁️ IMA同步...")
    if ima_syncer.rate_limited:
        print("  ⚠️ IMA被限流，跳过")
    else:
        doc_name = Path(doc_file).stem if doc_file else "未命名"
        organized = ContentOrganizer().clean_text(text)
        ima_id = ima_syncer.sync_note(doc_name, organized, theme, content_hash)
        if ima_id:
            print(f"  ✓ IMA同步成功")
        else:
            print("  ⚠️ IMA同步失败")

    # 7. 图片归档（按主题分类）
    print("\n📦 归档图片...")
    archived_path = archiver.archive_image(image_path, theme)
    if archived_path:
        archived_name = Path(archived_path).name
        archived_dir = Path(archived_path).parent.name
        print(f"  ✓ 已归档: 已处理图片/{archived_dir}/{archived_name}")

    return {
        'image': image_name,
        'source_folder': source_folder,
        'text_length': len(text),
        'theme': theme,
        'doc_file': doc_file,
        'is_duplicate': False,
        'content_hash': content_hash
    }


def main():
    print("=" * 60)
    print("全自动化图片处理工具 V4.0")
    print("OCR → 主题分类 → 内容合并 → 文档生成 → 按主题归档")
    print("=" * 60)

    # 初始化组件
    print("\n[1/6] 初始化OCR引擎...")
    ocr = MultiEngineOCR()
    if not ocr.current_engine:
        print("❌ 没有可用的OCR引擎!")
        return

    print("\n[2/6] 初始化主题分类器...")
    classifier = ThemeClassifier()

    print("\n[3/6] 初始化文档生成器...")
    doc_gen = DocumentGenerator()

    print("\n[4/6] 初始化IMA同步器...")
    ima_syncer = IMASyncer()
    if ima_syncer.rate_limited:
        print("  ⚠️ IMA被限流，本次将跳过IMA同步")

    print("\n[5/6] 初始化图片归档器...")
    archiver = ImageArchiver()

    print("\n[6/6] 扫描待处理图片...")
    source_dir = Path('待处理图片')
    if not source_dir.exists():
        print("❌ 待处理图片目录不存在!")
        return

    images = []
    for ext in ['*.jpg', '*.png', '*.jpeg', '*.webp', '*.bmp']:
        images.extend(source_dir.rglob(ext))

    if not images:
        print("❌ 未找到待处理图片")
        return

    total = len(images)
    print(f"✓ 找到 {total} 张图片")
    print(f"  子文件夹: {[d.name for d in source_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]}")

    # 初始化进度条
    progress = ProgressBar(total, prefix="📊 处理进度")

    # 批量处理
    results = []
    start_time = time.time()
    progress.start()

    for i, img_path in enumerate(images, 1):
        try:
            result = process_single_image(
                ocr, classifier, doc_gen, ima_syncer, archiver,
                str(img_path), i, total, progress
            )
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n  ✗ 处理失败: {e}")
            logger.error(f"处理失败 {img_path}: {e}")

    progress.finish()
    
    # 统计
    elapsed = time.time() - start_time

    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)
    print(f"总计处理: {len(results)}/{total} 张")
    print(f"总耗时: {elapsed:.1f} 秒")

    # 主题分布
    if results:
        print("\n📊 主题分布:")
        themes = Counter(r['theme'] for r in results if not r.get('is_duplicate'))
        for theme, count in themes.most_common():
            print(f"  - {theme}: {count} 张")

    # 源文件夹分布
    if results:
        print("\n📁 源文件夹分布:")
        folders = Counter(r['source_folder'] for r in results if not r.get('is_duplicate'))
        for folder, count in folders.most_common():
            print(f"  - {folder}: {count} 张")

    # 重复检测
    dup_count = sum(1 for r in results if r.get('is_duplicate'))
    if dup_count > 0:
        print(f"\n🔍 重复检测: 跳过 {dup_count} 条重复内容")

    # 归档统计
    archive_stats = archiver.get_archive_stats()
    print(f"\n📦 归档统计:")
    print(f"  - 本次归档: {archive_stats['archived_count']} 张")
    print(f"  - 已归档总数: {archive_stats['total_archived']} 张")
    if archive_stats['subdirs']:
        print(f"  - 子文件夹:")
        for subdir, count in archive_stats['subdirs'].items():
            print(f"    • {subdir}: {count} 张")

    if ima_syncer.rate_limited:
        print(f"\n☁️ IMA: 被限流，请明天再试")

    print("\n" + "=" * 60)

    # 保存报告
    report_file = Path('处理结果/处理报告.json')
    report = {
        'timestamp': datetime.now().isoformat(),
        'version': 'V4.0',
        'total_images': total,
        'processed': len(results),
        'duplicates': dup_count,
        'archived': archive_stats['archived_count'],
        'elapsed_seconds': elapsed,
        'theme_stats': dict(Counter(r['theme'] for r in results if not r.get('is_duplicate'))),
        'folder_stats': dict(Counter(r['source_folder'] for r in results if not r.get('is_duplicate'))),
        'results': [{k: v for k, v in r.items() if k not in ['doc_file']} for r in results]
    }
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📊 报告已保存: {report_file}")


if __name__ == '__main__':
    main()
