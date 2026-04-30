import os, json
from dotenv import load_dotenv
import requests

load_dotenv()
client_id = os.getenv('IMA_OPENAPI_CLIENTID', '')
api_key = os.getenv('IMA_OPENAPI_APIKEY', '')
base_url = 'https://ima.qq.com/openapi/note/v1'

with open('ima_debug.txt', 'w', encoding='utf-8') as f:
    f.write(f"ClientID: {client_id}\n")
    f.write(f"APIKey: {api_key[:20]}...\n\n")

    headers = {
        'ima-openapi-clientid': client_id,
        'ima-openapi-apikey': api_key,
        'Content-Type': 'application/json'
    }

    # 测试 import_doc
    url = base_url + '/import_doc'
    payload = {'content_format': 1, 'content': '# 测试\n\n测试内容'}

    f.write('测试 import_doc API...\n')
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        f.write(f'状态码: {resp.status_code}\n')
        f.write(f'响应: {resp.text}\n\n')

        result = resp.json()
        f.write('JSON字段:\n')
        for k, v in result.items():
            f.write(f'  {k}: {str(v)[:200]}\n')
    except Exception as e:
        f.write(f'错误: {e}\n')

    f.write('\n测试完成\n')
