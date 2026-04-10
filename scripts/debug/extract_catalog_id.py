import requests
import re
import time
import json

# First, get the product page to extract catalog ID
url = "https://www.mercadolibre.com.co/berberina-500-mg-60-capsulas/up/MCOU2420507475"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

session = requests.Session()

print("Fetching product page...")
time.sleep(2)  # Wait to avoid rate limiting

response = session.get(url, headers=headers, timeout=30)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    html = response.text
    
    # Look for catalog ID in the HTML
    # Common patterns: MCO followed by digits
    mco_matches = re.findall(r'MCO\d+', html)
    unique_mco = list(set(mco_matches))
    print(f"\nFound {len(unique_mco)} unique MCO references:")
    for m in unique_mco:
        print(f"  {m}")
    
    # Look for object_id or catalog_id in JSON data
    json_patterns = [
        r'"catalog_id"\s*:\s*"([^"]+)"',
        r'"objectId"\s*:\s*"([^"]+)"',
        r'"catalogItemId"\s*:\s*"([^"]+)"',
        r'"itemId"\s*:\s*"([^"]+)"',
        r'"id"\s*:\s*"([^"]+)"',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, html)
        if matches:
            print(f"\nPattern '{pattern}' found: {matches[:5]}")
    
    # Look for reviews API URL
    review_api = re.findall(r'/noindex/catalog/reviews/[^"\s]+', html)
    if review_api:
        print(f"\nReviews API URLs found:")
        for r in review_api:
            print(f"  {r[:150]}")
    
    # Look for iframe src
    iframe_srcs = re.findall(r'iframe[^>]+src=["\']([^"\']+)["\']', html)
    if iframe_srcs:
        print(f"\nIframe sources:")
        for src in iframe_srcs:
            print(f"  {src[:200]}")
    
    # Look for "reviews" or "opiniones" links
    review_links = re.findall(r'href="([^"]*(?:review|opinion|rating|calificacion)[^"]*)"', html, re.IGNORECASE)
    if review_links:
        print(f"\nReview-related links:")
        for link in review_links:
            print(f"  {link[:200]}")
    
    # Look for data-testid attributes related to reviews
    testids = re.findall(r'data-testid="([^"]*(?:review|rating|opinion)[^"]*)"', html, re.IGNORECASE)
    if testids:
        print(f"\nReview-related data-testid:")
        for tid in testids:
            print(f"  {tid}")
    
    # Look for any JSON-LD or structured data
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, re.DOTALL)
    if json_ld:
        print(f"\nJSON-LD data found ({len(json_ld)} blocks)")
        for i, block in enumerate(json_ld):
            try:
                data = json.loads(block)
                print(f"  Block {i}: {json.dumps(data, indent=2)[:500]}")
            except:
                print(f"  Block {i}: (invalid JSON)")
    
    # Look for the product ID in the URL pattern
    product_id_match = re.search(r'/up/(MCOU\d+)', url)
    if product_id_match:
        publication_id = product_id_match.group(1)
        print(f"\nPublication ID: {publication_id}")
        
        # Try to get product info from ML API
        api_url = f"https://api.mercadolibre.com/items/{publication_id}"
        print(f"Fetching from ML API: {api_url}")
        time.sleep(1)
        
        api_response = session.get(api_url, headers={"User-Agent": headers["User-Agent"]}, timeout=30)
        if api_response.status_code == 200:
            product_data = api_response.json()
            print(f"\nProduct data keys: {list(product_data.keys())}")
            print(f"Title: {product_data.get('title')}")
            print(f"Category ID: {product_data.get('category_id')}")
            print(f"Site ID: {product_data.get('site_id')}")
            
            # Look for catalog product ID
            if 'catalog_product_id' in product_data:
                print(f"Catalog Product ID: {product_data['catalog_product_id']}")
            
            # The domain_id might help
            if 'domain_id' in product_data:
                print(f"Domain ID: {product_data['domain_id']}")
        else:
            print(f"API response: {api_response.status_code}")
            print(api_response.text[:500])
else:
    print(f"Failed to fetch page: {response.status_code}")
    print(response.text[:500])
