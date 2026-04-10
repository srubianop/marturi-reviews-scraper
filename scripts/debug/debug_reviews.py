from playwright.sync_api import sync_playwright
import time
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="es-CO",
        timezone_id="America/Bogota"
    )
    page = context.new_page()
    
    # Block some tracking to speed up
    page.route("**/analytics/**", lambda route: route.abort())
    page.route("**/track/**", lambda route: route.abort())
    
    page.goto('https://www.mercadolibre.com.co/berberina-500-mg-60-capsulas/up/MCOU2420507475', wait_until='networkidle', timeout=60000)
    time.sleep(5)
    
    # Accept cookies if present
    cookie_btn = page.query_selector("button.cookie-consent-banner-opt-out__action--primary")
    if cookie_btn:
        cookie_btn.click()
        time.sleep(1)
        print("Accepted cookies")
    
    # Get page title and URL
    print(f'Title: {page.title()}')
    print(f'URL: {page.url}')
    
    # Get visible text
    text = page.inner_text('body')
    print(f'\nBody text length: {len(text)}')
    print(f'First 500 chars: {text[:500]}')
    
    # Check for CAPTCHA or bot detection
    if 'captcha' in text.lower() or 'robot' in text.lower() or 'verificación' in text.lower():
        print('\n⚠️ CAPTCHA or bot detection detected!')
    
    # Check for any element mentioning MCO
    content = page.content()
    mco_matches = re.findall(r'MCO\d+', content)
    print(f'\nFound {len(mco_matches)} MCO references')
    unique_mco = list(set(mco_matches))[:30]
    for m in unique_mco:
        print(f'  {m}')
    
    # Try to find any iframe
    iframes = page.query_selector_all('iframe')
    print(f'\nFound {len(iframes)} iframes')
    for i, iframe in enumerate(iframes):
        src = iframe.get_attribute('src') or '<no src>'
        print(f'  iframe[{i}]: {src[:200]}')
    
    # Look for review-related links
    review_links = page.query_selector_all('a[href*="review"], a[href*="opinion"], a[href*="rating"]')
    print(f'\nFound {len(review_links)} review-related links')
    for link in review_links:
        href = link.get_attribute('href')
        text_link = link.inner_text()
        print(f'  href={href[:150]} text={text_link[:80]}')
    
    # Scroll to bottom and wait
    page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(3)
    
    # Check iframes again after scroll
    iframes2 = page.query_selector_all('iframe')
    print(f'\nAfter scroll: {len(iframes2)} iframes')
    for i, iframe in enumerate(iframes2):
        src = iframe.get_attribute('src') or '<no src>'
        print(f'  iframe[{i}]: {src[:200]}')
    
    # Check MCO after scroll
    content2 = page.content()
    mco_matches2 = re.findall(r'MCO\d+', content2)
    print(f'\nAfter scroll: {len(mco_matches2)} MCO references')
    unique_mco2 = list(set(mco_matches2))[:30]
    for m in unique_mco2:
        print(f'  {m}')
    
    browser.close()
