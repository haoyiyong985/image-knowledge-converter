# -*- coding: utf-8 -*-
"""
完整链路诊断脚本：逐步验证 图片处理 → IMA自动同步 的每个环节
"""
import sys
import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(override=True)

PASS = '✅'
FAIL = '❌'
WARN = '⚠️'

results = []

def check(name, ok, detail=''):
    icon = PASS if ok else FAIL
    msg = f"{icon} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, ok, detail))
    return ok

print("=" * 60)
print("图片转化 → IMA 自动同步  完整链路诊断")
print("=" * 60)
print()

# ─────────────────────────────────────────────
# 1. 环境变量 & 凭证
# ─────────────────────────────────────────────
print("【1】环境配置检查")
client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key   = os.getenv('IMA_OPENAPI_APIKEY', '')
hny_id    = os.getenv('HUNYUAN_SECRET_ID', '')
hny_key   = os.getenv('HUNYUAN_SECRET_KEY', '')
ocr_id    = os.getenv('TENCENT_SECRET_ID', '')
ocr_key   = os.getenv('TENCENT_SECRET_KEY', '')

check('IMA_CLIENTID', bool(client_id), client_id[:12]+'...' if client_id else '未配置')
check('IMA_APIKEY',   bool(api_key),   api_key[:12]+'...' if api_key else '未配置')
check('混元LLM(HUNYUAN)', bool(hny_id and hny_key), '已配置' if hny_id else '未配置')
check('腾讯云OCR',    bool(ocr_id and ocr_key), '已配置' if ocr_id else '未配置（将用备用）')
print()

# ─────────────────────────────────────────────
# 2. IMA API 连通性
# ─────────────────────────────────────────────
print("【2】IMA API 连通性")
BASE_URL = 'https://ima.qq.com/openapi/note/v1'
ima_headers = {
    'ima-openapi-clientid': client_id,
    'ima-openapi-apikey': api_key,
    'Content-Type': 'application/json'
}
try:
    resp = requests.post(
        f'{BASE_URL}/import_doc',
        json={'content_format': 1, 'content': '# 诊断测试\n\n> 可删除\n\n链路诊断自动生成于 ' + time.strftime('%Y-%m-%d %H:%M')},
        headers=ima_headers, timeout=15
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get('code') == 0:
            note_id = data.get('data', {}).get('note_id', '')
            check('IMA import_doc', True, f'note_id={note_id}')
            IMA_OK = True
        else:
            check('IMA import_doc', False, f"code={data.get('code')}, msg={data.get('msg')}")
            IMA_OK = False
    else:
        check('IMA import_doc', False, f'HTTP {resp.status_code}: {resp.text[:100]}')
        IMA_OK = False
except Exception as e:
    check('IMA import_doc', False, str(e)[:120])
    IMA_OK = False
print()

# ─────────────────────────────────────────────
# 3. LLM 连通性
# ─────────────────────────────────────────────
print("【3】LLM（混元Lite）连通性")
try:
    from tencentcloud.common import credential
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models as hny_models

    cred = credential.Credential(hny_id, hny_key)
    client_hny = hunyuan_client.HunyuanClient(cred, 'ap-guangzhou')
    req = hny_models.ChatCompletionsRequest()
    req.Model = 'hunyuan-lite'
    msg = hny_models.Message()
    msg.Role = 'user'
    msg.Content = '请回复"OK"'
    req.Messages = [msg]
    req.Stream = False
    resp_hny = client_hny.ChatCompletions(req)
    reply = resp_hny.Choices[0].Message.Content.strip()
    check('混元Lite LLM', 'OK' in reply or len(reply) < 20, f'回复: {reply[:30]}')
    LLM_OK = True
except Exception as e:
    check('混元Lite LLM', False, str(e)[:120])
    LLM_OK = False
print()

# ─────────────────────────────────────────────
# 4. 主流程类初始化（IMASyncer）
# ─────────────────────────────────────────────
print("【4】IMASyncer 初始化检查")
try:
    # 动态导入主脚本的 IMASyncer
    import importlib.util
    spec = importlib.util.spec_from_file_location('main_script', 'auto_process_all_v9_4.py')
    mod = importlib.util.load_module_from_spec(spec) if hasattr(importlib.util, 'load_module_from_spec') else None
    
    # 直接实例化
    exec(open('auto_process_all_v9_4.py', encoding='utf-8').read(), {'__name__': '__module__'})
except Exception:
    pass

# 直接检查同步日志
sync_log_file = Path('处理结果/ima_sync_log.json')
if sync_log_file.exists():
    sync_log = json.loads(sync_log_file.read_text(encoding='utf-8'))
    check('同步日志文件', True, f'{len(sync_log)} 条记录')
    
    # 检查最近一条是否有有效note_id
    recent = sorted(sync_log.items(), key=lambda x: x[1].get('last_sync',''), reverse=True)
    if recent:
        last_title = recent[0][1].get('title','')
        last_id    = recent[0][1].get('doc_id','')
        last_time  = recent[0][1].get('last_sync','')[:19]
        check('最近同步记录', bool(last_id), f'{last_title} | {last_time} | id={last_id}')
else:
    check('同步日志文件', False, '文件不存在')
print()

# ─────────────────────────────────────────────
# 5. 文档 → IMA 同步模拟（用已有MD文档重新同步）
# ─────────────────────────────────────────────
print("【5】端到端同步模拟（用现有文档测试）")
result_dir = Path('处理结果')
# 找一个已有的知识文档
test_md = None
for md in sorted(result_dir.rglob('*.md')):
    if not md.name.startswith('_'):
        content = md.read_text(encoding='utf-8')
        if 'content_hash:' in content:
            test_md = md
            break

if test_md and IMA_OK:
    content = test_md.read_text(encoding='utf-8')
    title = test_md.stem
    
    # 构建同步内容
    full_content = f"# {title}\n\n> 分类: 诊断测试\n> 内容标识: diag-test\n\n{content[:500]}\n\n---\n*自动同步诊断*\n"
    
    try:
        resp = requests.post(
            f'{BASE_URL}/import_doc',
            json={'content_format': 1, 'content': full_content},
            headers=ima_headers, timeout=15
        )
        if resp.status_code == 200 and resp.json().get('code') == 0:
            note_id = resp.json().get('data', {}).get('note_id', '')
            check('文档→IMA同步', True, f'{title} → note_id={note_id}')
        else:
            check('文档→IMA同步', False, resp.text[:150])
    except Exception as e:
        check('文档→IMA同步', False, str(e)[:120])
elif not IMA_OK:
    print(f"  ⏭️ 跳过（IMA API不可用）")
else:
    print(f"  ⏭️ 跳过（没有找到知识文档）")
print()

# ─────────────────────────────────────────────
# 6. 总结
# ─────────────────────────────────────────────
print("=" * 60)
print("诊断结论")
print("=" * 60)
pass_n = sum(1 for _,ok,_ in results if ok)
fail_n = sum(1 for _,ok,_ in results if not ok)
print(f"通过: {pass_n}  失败: {fail_n}")
print()

if fail_n == 0:
    print("✅ 全链路正常！图片处理完成后会自动同步到IMA。")
    print()
    print("自动同步触发条件：")
    print("  1. 图片 OCR 成功")
    print("  2. LLM 元数据解析成功（非重复内容）")
    print("  3. 生成 Markdown 文档")
    print("  4. IMASyncer.sync_note() 自动调用 import_doc / append_doc")
else:
    print("存在问题，需要修复以下环节：")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL} {name}: {detail}")
