# -*- coding: utf-8 -*-
"""
完整链路诊断脚本（修正版）：用正确的环境变量名验证
图片处理 → IMA自动同步 的每个环节
"""
import sys
import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

PASS = 'OK'
FAIL = 'FAIL'

results = []

def check(name, ok, detail=''):
    icon = '✅' if ok else '❌'
    msg = f"  {icon} {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, ok, detail))
    return ok

print("=" * 60)
print("图片转化 → IMA 自动同步  完整链路诊断（修正版）")
print("=" * 60)
print()

# ─────────────────────────────────────────────
# 1. 环境变量
# ─────────────────────────────────────────────
print("【1】环境配置检查")
client_id  = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key    = os.getenv('IMA_OPENAPI_APIKEY', '')
tencent_id = os.getenv('TENCENT_SECRET_ID', '')   # 混元 + OCR 共用
tencent_key= os.getenv('TENCENT_SECRET_KEY', '')
silicon_key= os.getenv('SILICONFLOW_API_KEY', '')
baidu_id   = os.getenv('BAIDU_APP_ID', '')

check('IMA_CLIENTID',        bool(client_id),    client_id[:12]+'...' if client_id else '未配置')
check('IMA_APIKEY',          bool(api_key),      api_key[:12]+'...' if api_key else '未配置')
check('腾讯云(OCR+混元)',    bool(tencent_id and tencent_key), '已配置' if tencent_id else '未配置')
check('硅基流动(兜底LLM)',   bool(silicon_key),  '已配置' if silicon_key else '未配置')
check('百度OCR(备用)',        bool(baidu_id),     '已配置' if baidu_id else '未配置')
print()

# ─────────────────────────────────────────────
# 2. IMA API
# ─────────────────────────────────────────────
print("【2】IMA API 连通性")
BASE_URL = 'https://ima.qq.com/openapi/note/v1'
ima_headers = {
    'ima-openapi-clientid': client_id,
    'ima-openapi-apikey': api_key,
    'Content-Type': 'application/json'
}
IMA_OK = False
try:
    resp = requests.post(
        f'{BASE_URL}/import_doc',
        json={'content_format': 1, 'content': '# 诊断测试\n\n> 可删除，链路诊断自动生成于 ' + time.strftime('%Y-%m-%d %H:%M')},
        headers=ima_headers, timeout=15
    )
    if resp.status_code == 200 and resp.json().get('code') == 0:
        note_id = resp.json().get('data', {}).get('note_id', '')
        IMA_OK = check('IMA import_doc', True, f'note_id={note_id}')
    else:
        check('IMA import_doc', False, f'HTTP {resp.status_code}: {resp.text[:120]}')
except Exception as e:
    check('IMA import_doc', False, str(e)[:120])
print()

# ─────────────────────────────────────────────
# 3. 混元Lite LLM
# ─────────────────────────────────────────────
print("【3】LLM（混元Lite）连通性")
LLM_OK = False
try:
    from tencentcloud.hunyuan.v20230901 import hunyuan_client, models as hm_models
    from tencentcloud.common.credential import Credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile

    hp = HttpProfile()
    hp.endpoint = "hunyuan.tencentcloudapi.com"
    hp.reqTimeout = 10
    cp = ClientProfile()
    cp.httpProfile = hp
    client_hny = hunyuan_client.HunyuanClient(
        Credential(tencent_id, tencent_key), "ap-guangzhou", cp
    )
    req = hm_models.ChatCompletionsRequest()
    req.Model = "hunyuan-lite"
    req.Messages = [{"Role": "user", "Content": "请回复OK"}]
    req.Stream = False
    resp_hny = client_hny.ChatCompletions(req)
    reply = resp_hny.Choices[0].Message.Content.strip()
    LLM_OK = check('混元Lite', True, f'回复: {reply[:30]}')
except Exception as e:
    check('混元Lite', False, str(e)[:120])
print()

# ─────────────────────────────────────────────
# 4. 硅基流动 LLM（兜底）
# ─────────────────────────────────────────────
print("【4】LLM（硅基流动）连通性")
SILICON_OK = False
try:
    model = os.getenv('SILICONFLOW_MODEL', 'Qwen/Qwen2.5-7B-Instruct')
    resp_sf = requests.post(
        'https://api.siliconflow.cn/v1/chat/completions',
        json={
            'model': model,
            'messages': [{'role': 'user', 'content': '请回复OK'}],
            'max_tokens': 10
        },
        headers={'Authorization': f'Bearer {silicon_key}', 'Content-Type': 'application/json'},
        timeout=20
    )
    if resp_sf.status_code == 200:
        reply_sf = resp_sf.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        SILICON_OK = check('硅基流动', True, f'模型={model} 回复={reply_sf[:20]}')
    else:
        check('硅基流动', False, f'HTTP {resp_sf.status_code}: {resp_sf.text[:120]}')
except Exception as e:
    check('硅基流动', False, str(e)[:120])
print()

# ─────────────────────────────────────────────
# 5. 同步日志文件状态
# ─────────────────────────────────────────────
print("【5】同步日志状态")
sync_log_file = Path('处理结果/ima_sync_log.json')
sync_log = {}
if sync_log_file.exists():
    sync_log = json.loads(sync_log_file.read_text(encoding='utf-8'))
    check('同步日志文件', True, f'{len(sync_log)} 条记录')
    recent = sorted(sync_log.items(), key=lambda x: x[1].get('last_sync',''), reverse=True)
    if recent:
        t = recent[0][1]
        check('最近同步记录', True, f"{t.get('title','')} | {t.get('last_sync','')[:19]}")
else:
    check('同步日志文件', False, '文件不存在')
print()

# ─────────────────────────────────────────────
# 6. 端到端：已有MD文档 → IMA
# ─────────────────────────────────────────────
print("【6】文档→IMA 端到端同步测试")
result_dir = Path('处理结果')
test_md = None
for md in sorted(result_dir.rglob('*.md')):
    if not md.name.startswith('_') and not md.name.endswith('报告.md'):
        c = md.read_text(encoding='utf-8')
        if 'content_hash:' in c:
            test_md = md
            break

if test_md and IMA_OK:
    c = test_md.read_text(encoding='utf-8')
    full_c = f"# {test_md.stem} (诊断)\n\n{c[:300]}\n\n---\n*诊断脚本生成*\n"
    try:
        r2 = requests.post(f'{BASE_URL}/import_doc',
                           json={'content_format': 1, 'content': full_c},
                           headers=ima_headers, timeout=15)
        if r2.status_code == 200 and r2.json().get('code') == 0:
            nid = r2.json().get('data', {}).get('note_id', '')
            check('文档→IMA同步', True, f'{test_md.stem} → note_id={nid}')
        else:
            check('文档→IMA同步', False, r2.text[:150])
    except Exception as e:
        check('文档→IMA同步', False, str(e)[:100])
elif not IMA_OK:
    print("  ⏭️ 跳过（IMA API不可用）")
else:
    print("  ⏭️ 跳过（无知识文档）")
print()

# ─────────────────────────────────────────────
# 总结
# ─────────────────────────────────────────────
print("=" * 60)
print("诊断结论")
print("=" * 60)
pass_n = sum(1 for _,ok,_ in results if ok)
fail_n = sum(1 for _,ok,_ in results if not ok)
print(f"  通过: {pass_n} 项  失败: {fail_n} 项")
print()

if IMA_OK and (LLM_OK or SILICON_OK):
    print("✅ 核心链路正常！图片处理完成后会自动同步到IMA。")
    print()
    print("  自动同步工作流程：")
    print("  图片 → OCR识别 → LLM分析(分类+命名+整理)")
    print("         ↓ 非重复内容")
    print("         生成 Markdown 文档")
    print("         ↓ 自动调用 IMASyncer.sync_note()")
    print("         IMA import_doc / append_doc")
    print("         ↓")
    print("         ✅ 文档同步到IMA，记录到 ima_sync_log.json")
    if not LLM_OK and SILICON_OK:
        print()
        print("  ⚠️  混元Lite连接有异常，但硅基流动可作为兜底LLM正常运行")
else:
    print("❌ 存在阻断问题：")
    for name, ok, detail in results:
        if not ok:
            print(f"  • {name}: {detail}")
    if not (LLM_OK or SILICON_OK):
        print()
        print("  ⚠️ LLM全部不可用时，图片处理会失败（_skip=True），文档不会生成，IMA也不会同步")
