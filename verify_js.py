import re
import subprocess
import os

with open("D:/Blind_SMart_Glasses/index.html", "r", encoding="utf-8") as f:
    html = f.read()

scripts = re.findall(r"<script(?![^>]*src=)[^>]*>(.*?)</script>", html, re.DOTALL)
print(f"Found {len(scripts)} inline script blocks")
for i, s in enumerate(scripts):
    js_filename = f"temp_check_{i}.js"
    with open(js_filename, "w", encoding="utf-8") as f_js:
        f_js.write(s)
    res = subprocess.run(["node", "--check", js_filename], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Script {i}: JS SYNTAX OK!")
    else:
        print(f"Script {i} ERROR:\n", res.stderr)
    if os.path.exists(js_filename):
        os.remove(js_filename)
