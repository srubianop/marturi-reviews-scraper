---
name: ml-reviews-scraper
description: >
  Scrapes all reviews from a Mercado Libre product URL and exports them as a
  Judge.me-compatible CSV with Colombian names, realistic emails, and image URLs.
  Trigger: When the user wants to scrape Mercado Libre reviews, export reviews
  to Judge.me, import reviews to Shopify, scrape product reviews from ML,
  "scrapear reviews", "reviews de mercado libre", "importar reviews",
  "subir reviews a judge.me", "reviews judge.me", "scraping ML".
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

## When to Use

- User provides one or more Mercado Libre product URLs and wants reviews exported
- User needs to import reviews into Judge.me (Shopify)
- User wants to scrape reviews with images, ratings, and dates
- User needs realistic reviewer names and emails (not "Cliente verificado")

## Critical Patterns

### Architecture

The scraper uses a **hybrid approach**:
1. **API for text** — ML's internal API `/noindex/catalog/reviews/{objectId}/search` returns review text, ratings, dates. Paginated with `offset`/`limit` (max **15** per page). Called from the product page context to maintain session cookies.
2. **DOM for images** — The API does NOT return image URLs. Navigate to the iframe reviews page, scroll progressively to lazy-load all reviews, then extract image URLs from the DOM. Match images to reviews by body text.

### Key Technical Discoveries

| Discovery | Detail |
|-----------|--------|
| API endpoint | `/noindex/catalog/reviews/MCO{catalogId}/search` |
| Max limit per page | **15** (50 returns 400) |
| Must call from product page | Navigating away loses session cookies → 400 errors |
| Image URLs in DOM | `img.ui-review-capability-carousel__img` inside `.ui-review-capability-comments__comment` |
| Thumbnail → full size | Replace `D_NQ_NP_2X_` with `D_NQ_NP_` in URL |
| Image matching | Match by first 60 chars of review body text |
| CSV encoding | Use `utf-8-sig` (BOM) so Excel opens accents correctly |
| Judge.me date format | `YYYY-MM-DD HH:MM:SS UTC` |
| Multiple images | Separated by `;` in `picture_urls` column |

### Workflow

```
1. User provides ML product URL + Shopify product_handle
2. Load product page → establish session/cookies
3. Extract object_id from iframe src (or construct from URL)
4. Call API paginated (limit=15) from product page context
5. Navigate to iframe URL → scroll progressively → extract image URLs
6. Match images to reviews by body text
7. Assign Colombian names + realistic emails
8. Output CSV with utf-8-sig encoding
```

## Code Examples

### Minimal usage — single product

```python
python scraper.py "https://www.mercadolibre.com.co/producto/p/MCO12345678" "mi-producto-handle"
```

### Multiple products

```python
python scraper.py \
  "https://www.mercadolibre.com.co/prod1/p/MCO111" "producto-uno" \
  "https://www.mercadolibre.com.co/prod2/p/MCO222" "producto-dos"
```

### API call pattern (from browser context)

```javascript
// MUST be called from the product page context (has cookies)
const url = "https://www.mercadolibre.com.co/noindex/catalog/reviews/MCO23764381/search"
  + "?objectId=MCO23764381&siteId=MCO&isItem=false"
  + "&offset=0&limit=15&x-is-webview=false"
  + "&brandId=2939674&domain_id=MCO-BODY_SKIN_CARE_PRODUCTS&category_id=MCO180916";

const response = await fetch(url, {
  credentials: 'include',
  headers: { 'Accept': 'application/json' }
});
const data = await response.json();
// data.reviews[].comment.content.text → review body
// data.reviews[].rating → 1-5
// data.reviews[].comment.date → "05 oct 2023"
```

### Image extraction from DOM

```javascript
const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
comments.forEach(comment => {
  const body = comment.querySelector('[data-testid="comment-content-component"]')?.innerText.trim();
  const images = comment.querySelectorAll('img.ui-review-capability-carousel__img');
  const urls = Array.from(images).map(img =>
    img.getAttribute('src').replace('D_NQ_NP_2X_', 'D_NQ_NP_')
  );
  // Match by body[:60] → urls
});
```

## Commands

```bash
# Single product
python scraper.py "ML_URL" "shopify-handle"

# Multiple products
python scraper.py "URL1" "handle1" "URL2" "handle2"

# Custom output file
python scraper.py "URL" "handle" -o custom_output.csv

# Headless mode (for servers)
python scraper.py "URL" "handle" --headless
```

## Resources

- **Template/sample**: `reviews_judgeme_template.csv` (solo encabezados; no es salida generada)
- **Template**: See [assets/scraper.py](assets/scraper.py) for the complete, production-ready scraper
- **CSV format**: Judge.me Direct Import expects: `title,body,rating,review_date,reviewer_name,reviewer_email,product_id,product_handle,reply,picture_urls`
- **Date conversion**: ML dates like `05 oct 2023` → `2023-10-05 00:00:00 UTC`
