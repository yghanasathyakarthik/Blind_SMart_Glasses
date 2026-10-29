import urllib.request, urllib.parse, json

def smart_web_search(q):
    s_url = f'https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(q)}&limit=1&namespace=0&format=json'
    req1 = urllib.request.Request(s_url, headers={'User-Agent': 'SmartGlassesAI/1.0'})
    try:
        with urllib.request.urlopen(req1, timeout=3) as r:
            data = json.loads(r.read().decode('utf-8'))
            if data[1]:
                exact_title = data[1][0]
                sum_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(exact_title)}'
                req2 = urllib.request.Request(sum_url, headers={'User-Agent': 'SmartGlassesAI/1.0'})
                with urllib.request.urlopen(req2, timeout=3) as r2:
                    sum_data = json.loads(r2.read().decode('utf-8'))
                    return f"{exact_title}: {sum_data.get('extract')[:200]}"
    except Exception as e:
        return f'Error: {e}'
    return 'No result found'

for q in ['Mark Manson', 'Subtle Art of Not Giving a Fuck', 'quantum computing', 'capital of France']:
    print(q, '->', smart_web_search(q))
