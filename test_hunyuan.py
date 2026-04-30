#!/usr/bin/env python3
"""测试混元Lite API连通性"""
import os, json, time, hmac, hashlib, datetime, requests
from dotenv import load_dotenv
load_dotenv()

secret_id = os.getenv('TENCENT_SECRET_ID', '')
secret_key = os.getenv('TENCENT_SECRET_KEY', '')
print(f'Key prefix: {secret_id[:6]}...')
print(f'Key length: {len(secret_id)}, {len(secret_key)}')

ts = int(time.time())
dt = datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
service = 'hunyuan'
host = 'hunyuan.tencentcloudapi.com'
ct = 'application/json; charset=utf-8'
payload = {'Model': 'hunyuan-lite', 'Messages': [{'Role': 'user', 'Content': '回复OK即可'}], 'Stream': False}
payload_str = json.dumps(payload, ensure_ascii=False)

canonical_headers = f'content-type:{ct}\nhost:{host}\nx-tc-action:chatcompletions\n'
signed_headers = 'content-type;host;x-tc-action'
hashed = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()
cr = f'POST\n/\n\n{canonical_headers}\n{signed_headers}\n{hashed}'

cred = f'{dt}/{service}/tc3_request'
sts = f'TC3-HMAC-SHA256\n{ts}\n{cred}\n' + hashlib.sha256(cr.encode('utf-8')).hexdigest()

def s(k, m):
    return hmac.new(k, m.encode('utf-8'), hashlib.sha256).digest()

sd = s(f'TC3{secret_key}'.encode('utf-8'), dt)
ss = s(sd, service)
ssi = s(ss, 'tc3_request')
sig = hmac.new(ssi, sts.encode('utf-8'), hashlib.sha256).hexdigest()

auth = f'TC3-HMAC-SHA256 Credential={secret_id}/{cred}, SignedHeaders={signed_headers}, Signature={sig}'
headers = {
    'Authorization': auth,
    'Content-Type': ct,
    'Host': host,
    'X-TC-Action': 'ChatCompletions',
    'X-TC-Version': '2023-09-01',
    'X-TC-Timestamp': str(ts)
}

print('Sending request...')
resp = requests.post(f'https://{host}', json=payload, headers=headers, timeout=10)
print(f'Status: {resp.status_code}')
rj = resp.json()
rd = rj.get('Response', {})
print(f'Response keys: {list(rd.keys())}')

if 'Error' in rd:
    e = rd['Error']
    print(f'>>> ERROR <<<')
    print(f'Code: {e.get("Code")}')
    print(f'Message: {e.get("Message")}')
elif 'Choices' in rd:
    c = rd['Choices'][0]['Message']['Content']
    print(f'Reply: {c[:200]}')
    print('>>> SUCCESS <<<')
else:
    print(f'Unknown response: {json.dumps(rd, ensure_ascii=False)[:500]}')
