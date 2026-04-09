from playwright.sync_api import sync_playwright
import time
import re
import json

with sync_playwright() as p:
    # Launch with visible browser
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="es-CO",
        timezone_id="America/Bogota"
    )
    page = context.new_page()
    
    # First, visit the homepage to get cookies
    print("Step 1: Visiting homepage...")
    page.goto('https://www.mercadolibre.com.co', wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    
    # Accept cookies
    cookie_btn = page.query_selector("button.cookie-consent-banner-opt-out__action--primary")
    if cookie_btn:
        cookie_btn.click()
        time.sleep(1)
        print("  Cookies accepted")
    
    # Check page content
    text = page.inner_text('body')
    print(f"  Homepage text length: {len(text)}")
    print(f"  First 200 chars: {text[:200]}")
    
    if 'error' in text.lower() or 'hubo un error' in text.lower():
        print("  ERROR: Homepage blocked")
        browser.close()
        exit()
    
    # Now search for the product
    print("\nStep 2: Searching for product...")
    page.goto('https://www.mercadolibre.com.co/jm/search#search_layout=grid&origin=header&search=berberina+500+mg+60+capsulas+puritans+pride', wait_until='domcontentloaded', timeout=60000)
    time.sleep(5)
    
    # Check if we got results
    text = page.inner_text('body')
    print(f"  Search page text length: {len(text)}")
    print(f"  First 300 chars: {text[:300]}")
    
    # Look for the specific product
    links = page.query_selector_all('a[href*="berberina"]')
    print(f"\n  Found {len(links)} berberina links")
    for link in links[:5]:
        href = link.get_attribute('href')
        title = link.inner_text()[:100]
        if title:
            print(f"  Title: {title}")
            print(f"  URL: {href}\n")
    
    # Look for any product links
    all_links = page.query_selector_all('a[href*="/up/"], a[href*="/p/"]')
    print(f"\n  Found {len(all_links)} product links")
    for link in all_links[:5]:
        href = link.get_attribute('href')
        title = link.inner_text()[:100]
        if title:
            print(f"  Title: {title}")
            print(f"  URL: {href}\n")
    
    # Look for MCO IDs
    content = page.content()
    mco_matches = re.findall(r'MCO\d+', content)
    unique_mco = list(set(mco_matches))
    print(f"\n  MCO references: {len(unique_mco)}")
    for m in unique_mco[:15]:
        print(f"    {m}")
    
    # Wait for user to see the browser
    print("\nBrowser will stay open for 30 seconds - check if it loaded properly")
    time.sleep(30)
    
    browser.close()
