with open(r'D:\Blind_SMart_Glasses\index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
script_m = re.search(r'<script>(.*?)</script>', text, re.DOTALL)
if script_m:
    s = script_m.group(1)
    lines = s.split('\n')
    balance = 0
    for idx, line in enumerate(lines):
        # ignore comments and string literals roughly
        line_clean = re.sub(r'//.*', '', line)
        line_clean = re.sub(r'/\*.*?\*/', '', line_clean)
        # count ( and )
        o = line_clean.count('(')
        c = line_clean.count(')')
        balance += (o - c)
        if balance < 0:
            print(f"Unbalanced at line {idx+1}: balance={balance}")
            print(f"  {line.strip()}")
            break
    print("Final balance:", balance)
