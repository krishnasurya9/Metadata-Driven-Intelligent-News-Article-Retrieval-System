import requests

def test_conn():
    url = "https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/config.json"
    print(f"Testing connection to {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Download successful!")
            print(response.text[:100])
        else:
            print("Failed to download.")
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    test_conn()
