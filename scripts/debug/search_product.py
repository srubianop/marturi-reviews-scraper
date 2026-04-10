import requests
import re
import time
import json

# Search for the product on Mercado Libre Colombia
search_url = "https://api.mercadolibre.com/sites/MCO/search"
params = {
    "q": "berberina 500 mg 60 capsulas puritans pride",
    "limit": 5
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

session = requests.Session()

print("Searching for product on ML API...")
time.sleep(2)

response = session.get(search_url, params=params, headers=headers, timeout=30)
print(f"Search Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    results = data.get('results', [])
    print(f"Found {len(results)} results\n")
    
    for i, item in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Title: {item.get('title')}")
        print(f"  ID: {item.get('id')}")
        print(f"  Permalink: {item.get('permalink')}")
        
        # Check for catalog_product_id
        catalog_id = item.get('catalog_product_id')
        if catalog_id:
            print(f"  Catalog Product ID: {catalog_id}")
        
        # Check for attributes
        attributes = item.get('attributes', [])
        for attr in attributes:
            if attr.get('id') in ['BRAND', 'MODEL']:
                print(f"  {attr['id']}: {attr.get('value_name')}")
        
        print()
        
        # If we found a catalog_product_id, try to get reviews
        if catalog_id:
            # The catalog_id might be just the numeric part
            catalog_num = re.search(r'MCO(\d+)', catalog_id)
            if catalog_num:
                catalog_num = catalog_num.group(1)
            else:
                catalog_num = catalog_id
            
            # Try to get reviews from the catalog API
            reviews_url = f"https://www.mercadolibre.com.co/noindex/catalog/reviews/{catalog_id}/search"
            reviews_params = {
                "objectId": catalog_id,
                "siteId": "MCO",
                "isItem": "false",
                "offset": 0,
                "limit": 15,
                "x-is-webview": "false"
            }
            
            print(f"  Trying reviews API with catalog_id: {catalog_id}")
            time.sleep(1)
            
            # We need cookies for this, so let's try the web approach
            print(f"  Would need to call from browser context")
            
else:
    print(f"Search failed: {response.status_code}")
    print(response.text[:500])
