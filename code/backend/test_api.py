import urllib.request
import urllib.error
import json
import time

BASE_URL = 'http://localhost:5000/api'

endpoints = [
    ('GET', '/health', None),
    ('GET', '/stats', None),
    ('POST', '/search', {"query": "technology AI dataset", "top_k": 5}),
    ('GET', '/metrics', None),
    ('GET', '/cdm/elbow', None),
    ('POST', '/cdm/cluster', {"n_clusters": 3}),
    ('POST', '/cdm/pca', {"n_clusters": 3, "sample_size": 200}),
    ('POST', '/cdm/classify', {}),
    ('POST', '/cdm/predict', {"text": "A new breakthrough in quantum computing and machine learning AI models."}),
    ('POST', '/cdm/association', {"min_support": 0.05, "min_confidence": 0.2}),
    ('POST', '/cdm/temporal', {}),
    ('POST', '/cdm/keywords', {"top_n": 10})
]

print("=== STARTING FULL IRT & CDM API TEST ===")
success = 0
for method, url, payload in endpoints:
    full_url = BASE_URL + url
    print(f"\nTesting {method} {full_url}...")
    try:
        t0 = time.time()
        if method == 'GET':
            req = urllib.request.Request(full_url)
        else:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(full_url, data=data, headers={'Content-Type': 'application/json'})
            
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data)
            dur = time.time() - t0
            status = res_json.get('status', 'unknown')
            print(f"SUCCESS ({dur:.2f}s) -> Status: {status}")
            d = res_json.get('data', {})
            if isinstance(d, dict):
                print(f"   Data Keys: {list(d.keys())[:8]}")
            success += 1
    except urllib.error.HTTPError as e:
        print(f"HTTP ERROR: {e.code} {e.reason}")
        print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"ERROR: {str(e)}")

print(f"\nPassed {success}/{len(endpoints)} tests.")