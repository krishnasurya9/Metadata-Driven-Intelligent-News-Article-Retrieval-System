import urllib.request
import json

def test_api(url, payload=None):
    try:
        req = urllib.request.Request(url, method='POST' if payload else 'GET')
        if payload:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(payload).encode()
        resp = urllib.request.urlopen(req)
        print(f'[OK] {url}')
        return json.loads(resp.read())
    except Exception as e:
        print(f'[FAIL] {url} - {e}')
        return None

print('--- Testing CDM Endpoints ---')
base = 'http://localhost:5000/api/cdm'

# Check datasets
r = test_api(f'{base}/datasets')
if r: print(f'Active Dataset: {r.get("data", {}).get("active_dataset")}')

# Test Stats
test_api(f'{base}/stats')

# Test PCA
test_api(f'{base}/pca', payload={'n_clusters': 2, 'sample_size': 100})

# Test Cluster
test_api(f'{base}/cluster', payload={'n_clusters': 2})

# Test Classify
test_api(f'{base}/classify')

print('Done testing CDM APIs.')
