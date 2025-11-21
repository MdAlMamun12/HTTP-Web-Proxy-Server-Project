import requests
import time

def test_proxy_cache():
    """Test script to populate cache with various requests"""
    
    proxies = {
        'http': 'http://localhost:8080',
        'https': 'http://localhost:8080'
    }
    
    test_urls = [
        'http://example.com',
        'http://httpbin.org/json',
        'http://httpbin.org/html',
        'http://httpbin.org/xml',
        'http://httpbin.org/robots.txt',
        'http://httpbin.org/user-agent'
    ]
    
    print("Testing proxy cache population...")
    
    for i, url in enumerate(test_urls, 1):
        try:
            print(f"Request {i}/{len(test_urls)}: {url}")
            response = requests.get(url, proxies=proxies, timeout=10)
            print(f"  Status: {response.status_code}, Size: {len(response.content)} bytes")
            time.sleep(1)  # Be nice to the servers
        except Exception as e:
            print(f"  Error: {e}")
    
    print("\nCache population test completed!")
    print("Check the web interface at http://localhost:5000 to see cached items.")

if __name__ == "__main__":
    test_proxy_cache()