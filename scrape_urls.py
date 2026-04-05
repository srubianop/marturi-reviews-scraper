"""Scrape reviews from direct ML product URLs - DOM scraping fallback."""
import sys, io, csv, json, time, random, re
from datetime import datetime
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

OUTPUT_FILE = "reviews_judgeme.csv"
FIELDNAMES = ["title","body","rating","review_date","reviewer_name","reviewer_email","product_id","product_handle","reply","picture_urls"]
MONTH_ES = {"ene":"01","feb":"02","mar":"03","abr":"04","may":"05","jun":"06","jul":"07","ago":"08","sep":"09","oct":"10","nov":"11","dic":"12"}

NOMBRES = ["Carlos Andres Rodriguez","Juan Pablo Martinez","Andres Felipe Gomez","Luis Fernando Lopez","Diego Alejandro Herrera","Camilo Andres Torres","Sebastian David Morales","Miguel Angel Castro","Jose David Vargas","Santiago Andres Ortiz","Daniel Esteban Ruiz","Felipe Andres Mendoza","Oscar Julian Diaz","Nicolas Andres Herrera","Alejandro Gomez Silva","David Santiago Reyes","Mateo Andres Jimenez","Julian David Pena","Esteban Camilo Rojas","Ricardo Andres Montoya","Maria Fernanda Lopez","Ana Maria Garcia","Laura Valentina Martinez","Carolina Andrea Rodriguez","Paola Andrea Gomez","Valentina Herrera","Daniela Alejandra Torres","Sofia Isabel Morales","Camila Andres Castro","Luisa Fernanda Vargas","Andrea Marcela Ortiz","Natalia Andrea Ruiz","Mariana Alejandra Mendoza","Isabella Sofia Diaz","Gabriela Maria Reyes","Paula Andrea Jimenez","Sara Valentina Pena","Juliana Andrea Rojas","Catalina Maria Montoya","Valeria Alejandra Salazar","Ximena Andrea Cardenas","Lina Marcela Medina","Diana Carolina Navarro","Karen Julieth Acosta","Leidy Johana Guzman","Angie Tatiana Vega","Jennifer Andrea Castillo","Claudia Marcela Leon","Gloria Stella Munoz","Sandra Milena Figueroa"]
DOMINIOS = ["gmail.com","hotmail.com","outlook.com","yahoo.com","live.com","gmail.com.co"]

URLS = [
    ("acido-alfa-lipoico-ala-biotina-600mg", "https://www.mercadolibre.com.co/acido-alfa-lipoico-ala-biotina-600mg-90-capsulas-antioxidante/up/MCOU3350893062"),
]

def parse_date(ds):
    ds = ds.strip().lower()
    p = ds.split()
    if len(p)==3:
        d,m,y = p
        mn = MONTH_ES.get(m[:3],"01")
        return f"{y}-{mn}-{d.zfill(2)} 00:00:00 UTC"
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

def gen_email(name, seed):
    random.seed(seed)
    parts = name.lower().split()
    dom = random.choice(DOMINIOS)
    if len(parts)>=2:
        a = re.sub(r'[^a-z]','',parts[0])
        b = re.sub(r'[^a-z]','',parts[1])
        return f"{a}.{b}{random.randint(1,99)}@{dom}"
    return f"{parts[0]}{random.randint(100,9999)}@{dom}" if parts else f"user{random.randint(1000,9999)}@{dom}"

def scrape_dom_reviews(page, url):
    """Scrape reviews by loading the review iframe directly and extracting from DOM."""
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)
    
    # Click "Mostrar todas las opiniones"
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
    time.sleep(2)
    page.evaluate("""
        () => {
            const btn = Array.from(document.querySelectorAll('button, a')).find(el =>
                el.innerText.includes('Mostrar todas las opiniones') ||
                el.innerText.includes('Ver todas las opiniones'));
            if (btn) btn.click();
        }
    """)
    time.sleep(3)
    
    # Find review iframe
    iframe_src = page.evaluate("""
        () => {
            for (const f of document.querySelectorAll('iframe')) {
                const s = f.getAttribute('src') || '';
                if (s.includes('catalog/reviews')) return s;
            }
            return null;
        }
    """)
    
    if not iframe_src:
        print("  No review iframe found")
        return []
    
    # Navigate directly to the iframe URL
    iframe_url = f"https://www.mercadolibre.com.co{iframe_src}" if iframe_src.startswith('/') else iframe_src
    print(f"  Loading review page: {iframe_url[:100]}...")
    
    page.goto(iframe_url, wait_until="domcontentloaded", timeout=20000)
    time.sleep(3)
    
    # Scroll to load ALL reviews
    prev = 0
    for _ in range(20):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        cur = page.evaluate("() => document.querySelectorAll('.ui-review-capability-comments__comment').length")
        if cur == prev:
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            cur = page.evaluate("() => document.querySelectorAll('.ui-review-capability-comments__comment').length")
            if cur == prev:
                break
        prev = cur
        print(f"  Loaded: {cur} reviews")
    
    print(f"  TOTAL reviews in DOM: {prev}")
    
    # Extract all review data from DOM
    reviews = page.evaluate("""
        () => {
            const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
            const reviews = [];
            
            comments.forEach(comment => {
                const contentEl = comment.querySelector('[data-testid="comment-content-component"]');
                const body = contentEl ? contentEl.innerText.trim() : '';
                if (!body) return;
                
                // Rating
                const stars = comment.querySelectorAll('.ui-review-capability-stars__star--active, .ui-review-capability-stars__star--filled');
                const rating = stars.length || 5;
                
                // Date
                const dateEl = comment.querySelector('.ui-review-capability-date__text');
                const date = dateEl ? dateEl.innerText.trim() : '';
                
                // Title (if any)
                const titleEl = comment.querySelector('.ui-review-capability-title__text');
                const title = titleEl ? titleEl.innerText.trim() : '';
                
                // Images
                const imgs = Array.from(comment.querySelectorAll('img.ui-review-capability-carousel__img'))
                    .map(i => (i.getAttribute('src')||'').replace('D_NQ_NP_2X_','D_NQ_NP_'))
                    .filter(u => u);
                
                reviews.push({
                    body: body,
                    rating: rating,
                    date: date,
                    title: title,
                    images: imgs,
                });
            });
            
            return reviews;
        }
    """)
    
    print(f"  Extracted: {len(reviews)} reviews with text")
    if reviews:
        print(f"  First: {reviews[0]['body'][:80]}")
        imgs_count = sum(1 for r in reviews if r['images'])
        print(f"  With images: {imgs_count}")
    
    return reviews

def main():
    # Load productos.json for Shopify ID mapping
    shopify_ids = {}
    try:
        with open("productos.json","r",encoding="utf-8") as f:
            for p in json.load(f):
                if p.get("handle") and p.get("shopify_id"):
                    shopify_ids[p["handle"]] = p["shopify_id"]
    except: pass

    registry = {}
    try:
        with open("reviews_registry.json","r",encoding="utf-8") as f:
            registry = json.load(f)
    except: pass

    all_formatted = []
    stats = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(viewport={"width":1280,"height":800}, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
        page = ctx.new_page()

        for handle, url in URLS:
            print(f"\n{'#'*60}")
            print(f"Scraping: {handle}")
            print(f"{'#'*60}")

            try:
                raw = scrape_dom_reviews(page, url)
                random.seed(42)
                names = random.sample(NOMBRES, min(len(NOMBRES), max(len(raw), 50)))
                while len(names) < len(raw):
                    names.extend(random.sample(NOMBRES, len(NOMBRES)))

                for i, r in enumerate(raw):
                    name = names[i % len(names)]
                    email = gen_email(name, i)
                    pics = ";".join(r['images']) if r.get('images') else ""

                    all_formatted.append({
                        "title": r.get('title','') or "Buena compra",
                        "body": r['body'],
                        "rating": int(r['rating']),
                        "review_date": parse_date(r.get('date','')),
                        "reviewer_name": name,
                        "reviewer_email": email,
                        "product_id": shopify_ids.get(handle, ""),
                        "product_handle": handle,
                        "reply": "",
                        "picture_urls": pics,
                    })

                print(f"  Formatted: {len(raw)} reviews")
                stats.append({"handle":handle,"status":"ok","reviews":len(raw)})

                registry.setdefault("products",{})[handle] = {"title":handle,"status":"success","reviews":len(raw),"matched_url":url,"last_scraped":datetime.now().strftime("%Y-%m-%d")}
                registry["total_reviews"] = sum(pp["reviews"] for pp in registry.get("products",{}).values() if pp.get("status")=="success")
                with open("reviews_registry.json","w",encoding="utf-8") as f:
                    json.dump(registry, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
                stats.append({"handle":handle,"status":f"error: {e}","reviews":0})

            time.sleep(random.uniform(2,4))

        browser.close()

    if all_formatted:
        import os
        exists = os.path.isfile(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0
        with open(OUTPUT_FILE, "a" if exists else "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not exists: w.writeheader()
            w.writerows(all_formatted)
        print(f"\n{'='*60}")
        print(f"CSV updated: {OUTPUT_FILE}")
        print(f"Reviews added: {len(all_formatted)}")
        print(f"{'='*60}")

    print("\nRESUMEN:")
    for s in stats:
        print(f"  {'OK' if s['status']=='ok' else 'FAIL'} {s['handle']}: {s['status']} ({s['reviews']} reviews)")

if __name__ == "__main__":
    main()
