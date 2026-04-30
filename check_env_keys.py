# -*- coding: utf-8 -*-
from dotenv import dotenv_values
env = dotenv_values('.env')
for k, v in sorted(env.items()):
    if any(x in k.upper() for x in ['HUNYUAN', 'SECRET', 'LLM', 'SILICON', 'KIMI', 'DOUBAO', 'API_KEY', 'APIKEY']):
        display = (v[:20] + '...') if v and len(v) > 20 else (v or '(空)')
        print(f'{k} = {display}')
print()
print('--- 全部Key ---')
for k in sorted(env.keys()):
    print(k)
