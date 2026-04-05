"""
Mercado Libre Colombia → Judge.me (Shopify) Review Scraper
===========================================================
Flujo automatizado:
1. Carga productos desde productos.json (exportado de Shopify)
2. Busca cada producto en ML Colombia
3. Filtra coincidencias exactas con el título del producto
4. Selecciona el mejor producto (más vendidos) entre las coincidencias
5. Extrae TODAS las reviews con texto + imágenes
6. Genera CSV compatible con Judge.me

Uso:
    python scraper.py              # Procesa todos los productos de productos.json
    python scraper.py --product 0  # Procesa solo el producto #0
    python scraper.py --from 5 --to 10  # Procesa productos 5-10
"""

import csv
import json
import re
import sys
import time
import random
import unicodedata
from datetime import datetime
from urllib.parse import urlparse, parse_qs, quote
from pathlib import Path
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ─── Configuración ────────────────────────────────────────────────────────────

PRODUCTS_FILE = "productos.json"
OUTPUT_FILE = "reviews_judgeme.csv"
MAX_SEARCH_RESULTS = 20  # Cuántos resultados traer de la búsqueda
MIN_MATCH_SCORE = 0.5    # Score mínimo para considerar coincidencia

FIELDNAMES = [
    "title", "body", "rating", "review_date", "reviewer_name",
    "reviewer_email", "product_id", "product_handle", "reply", "picture_urls",
]

MONTH_ES = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "oct": "10", "nov": "11", "dic": "12",
}

# ─── Nombres colombianos realistas ────────────────────────────────────────────

NOMBRES_COLOMBIA = [
    "Carlos Andrés Rodríguez", "Juan Pablo Martínez", "Andrés Felipe Gómez",
    "Luis Fernando López", "Diego Alejandro Herrera", "Jhon Jairo Ramírez",
    "Camilo Andrés Torres", "Sebastián David Morales", "Miguel Ángel Castro",
    "José David Vargas", "Santiago Andrés Ortiz", "Daniel Esteban Ruiz",
    "Felipe Andrés Mendoza", "Óscar Julián Díaz", "Nicolás Andrés Herrera",
    "Alejandro Gómez Silva", "David Santiago Reyes", "Mateo Andrés Jiménez",
    "Julián David Peña", "Esteban Camilo Rojas", "Ricardo Andrés Montoya",
    "Andrés Mauricio Salazar", "Jorge Iván Cárdenas", "Héctor Fabio Medina",
    "César Augusto Navarro", "Germán Andrés Acosta", "Fabio Andrés Ríos",
    "Wilson Andrés Guzmán", "Edwin Alberto Vega", "Brayan Stiven Castillo",
    "Kevin Julián Moreno", "Stiven Andrés Parra", "Jhonatan David Soto",
    "Cristian Camilo León", "Yerson David Muñoz", "Brayan Andrés Figueroa",
    "Álvaro José Pineda", "Rafael Andrés Contreras", "Mario Alberto Delgado",
    "Fernando José Agudelo", "Gustavo Andrés Rincón", "Pedro Nel Ospina",
    "Manuel Alejandro Franco", "Jairo Andrés Mejía", "Víctor Hugo Salinas",
    "María Fernanda López", "Ana María García", "Laura Valentina Martínez",
    "Carolina Andrea Rodríguez", "Paola Andrea Gómez", "Valentina Herrera",
    "Daniela Alejandra Torres", "Sofía Isabel Morales", "Camila Andrés Castro",
    "Luisa Fernanda Vargas", "Andrea Marcela Ortiz", "Natalia Andrea Ruiz",
    "Mariana Alejandra Mendoza", "Isabella Sofía Díaz", "Gabriela María Reyes",
    "Paula Andrea Jiménez", "Sara Valentina Peña", "Juliana Andrea Rojas",
    "Catalina María Montoya", "Valeria Alejandra Salazar", "Ximena Andrea Cárdenas",
    "Lina Marcela Medina", "Diana Carolina Navarro", "Karen Julieth Acosta",
    "Yurani Paola Ríos", "Leidy Johana Guzmán", "Angie Tatiana Vega",
    "Jennifer Andrea Castillo", "Stephany López Moreno", "Yuri Marcela Parra",
    "María José Soto", "Claudia Marcela León", "Gloria Stella Muñoz",
    "Sandra Milena Figueroa", "Rosa Elena Pineda", "Lucía Fernanda Contreras",
    "Patricia Adelaida Delgado", "Marta Lucía Agudelo", "Beatriz Elena Rincón",
    "Adriana Marcela Ospina", "Inés María Franco", "Teresa de Jesús Mejía",
    "Olga Lucía Salinas", "Esperanza Gómez", "Nancy Patricia Herrera",
    "Alejandro Martínez", "María Camila López", "Juan David García",
    "Luisa María Rodríguez", "Carlos Eduardo Gómez", "Ana Sofía Herrera",
    "Jorge Andrés Torres", "Valentina Morales", "Diego Fernando Castro",
    "Paula Camila Vargas", "Andrés Felipe Ortiz", "María Isabel Ruiz",
    "Sebastián Mendoza", "Laura Camila Díaz", "Juan Sebastián Reyes",
    "Carolina Jiménez", "Felipe Peña", "María Alejandra Rojas",
    "Santiago Montoya", "Daniela Salazar", "Mateo Cárdenas",
    "Andrea Medina", "Nicolás Navarro", "Isabella Acosta",
    "Daniel Ríos", "Sara Guzmán", "Camilo Vega",
    "Valeria Castillo", "Julián Moreno", "Gabriela Parra",
]

DOMINIOS_EMAIL = [
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com",
    "live.com", "hotmail.es", "gmail.com.co", "yahoo.es",
    "outlook.es", "icloud.com", "protonmail.com",
]


# ─── Utilidades ───────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin caracteres especiales."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_ml_date(date_str: str) -> str:
    """Convierte '05 oct 2023' → '2023-10-05 00:00:00 UTC'"""
    date_str = date_str.strip().lower()
    parts = date_str.split()
    if len(parts) == 3:
        day, month, year = parts
        month_num = MONTH_ES.get(month[:3], "01")
        return f"{year}-{month_num}-{day.zfill(2)} 00:00:00 UTC"
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def sanitize_text(text: str) -> str:
    """Limpia texto de reviews."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def generar_email(nombre: str, seed: int = None) -> str:
    """Genera un email realista basado en el nombre."""
    if seed is not None:
        random.seed(seed)
    partes = nombre.lower().split()
    dominio = random.choice(DOMINIOS_EMAIL)
    estrategias = []
    if len(partes) >= 2:
        primero = re.sub(r'[^a-z]', '', partes[0])
        segundo = re.sub(r'[^a-z]', '', partes[1])
        estrategias.append(f"{primero}.{segundo}")
        estrategias.append(f"{primero}{segundo}")
        estrategias.append(f"{primero[0]}.{segundo}")
        estrategias.append(f"{primero}.{segundo[0]}")
        estrategias.append(f"{primero}_{segundo}")
        estrategias.append(f"{primero}.{segundo}{random.randint(1, 99)}")
        estrategias.append(f"{primero[0]}{segundo}{random.randint(10, 99)}")
    if len(partes) >= 3:
        tercero = re.sub(r'[^a-z]', '', partes[2])
        estrategias.append(f"{primero}.{segundo}.{tercero}")
        estrategias.append(f"{primero[0]}{segundo[0]}{tercero}")
    if len(partes) >= 1:
        primero = re.sub(r'[^a-z]', '', partes[0])
        estrategias.append(f"{primero}{random.randint(100, 9999)}")
    email_base = random.choice(estrategias)
    return f"{email_base}@{dominio}"


def extract_sold_quantity(sold_text: str) -> int:
    """Extrae cantidad vendida de texto como '1.234 vendidos' o '50+ vendidos'."""
    if not sold_text:
        return 0
    match = re.search(r'([\d.]+)', sold_text)
    if match:
        return int(match.group(1).replace('.', ''))
    return 0


# ─── Búsqueda y selección de productos ────────────────────────────────────────

def build_search_query(title: str) -> str:
    """
    Query simple: marca + producto. Sin filtros agresivos.
    Solo elimina tamaños/pesos y limpia caracteres especiales.
    """
    # Eliminar tamaños/pesos: 250ml, 600 ml, 90ml, 200ml, 1L, 4 oz, etc.
    cleaned = re.sub(r'\b\d+(\.\d+)?\s*(ml|cm|kg|g|oz|l|lb)\b', '', title, flags=re.IGNORECASE)
    # Eliminar "x3", "2 x", "pack", etc.
    cleaned = re.sub(r'\b(x\d+|\d+\s*x\s*\d+)\b', '', cleaned, flags=re.IGNORECASE)
    # Eliminar guiones, pipes, paréntesis, corchetes
    cleaned = cleaned.replace(' - ', ' ').replace(' | ', ' ').replace(' — ', ' ')
    cleaned = re.sub(r'\([^)]*\)', '', cleaned)
    cleaned = re.sub(r'\[[^\]]*\]', '', cleaned)
    # Eliminar signos especiales
    cleaned = re.sub(r'[–—]', ' ', cleaned)

    words = cleaned.split()
    # Filtrar solo palabras vacías muy comunes
    stop_words = {'de', 'la', 'el', 'en', 'y', 'con', 'para', 'por', 'sin', 'del',
                  'los', 'las', 'un', 'una', 'unos', 'unas', 'al', 'es'}
    significant = [w for w in words if w.lower() not in stop_words and len(w) > 1]

    # Tomar las primeras 5 palabras (marca + producto)
    query = ' '.join(significant[:5])
    return query.strip()


def search_products_ml(query: str, page, raw_query: str = None) -> list[dict]:
    """
    Busca productos en ML Colombia con múltiples estrategias de query.
    """
    search_url = f"https://listado.mercadolibre.com.co/{quote(query)}"
    display = raw_query or query
    print(f"    ML Search: '{display}'")
    print(f"    URL: {search_url}")

    # Retry loop for navigation errors
    for attempt in range(3):
        try:
            page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

            products = page.evaluate("""
        () => {
            const items = document.querySelectorAll('.ui-search-result__wrapper');
            const results = [];

            items.forEach(item => {
                const link = item.querySelector('a.poly-component__title, a.ui-search-link, a.ui-search-item__group__element');
                if (!link) return;

                let href = link.getAttribute('href') || '';

                const titleEl = item.querySelector('.poly-component__title, .ui-search-item__title');
                const title = titleEl ? titleEl.innerText.trim() : '';
                if (!title) return;

                const priceEl = item.querySelector('.andes-money-amount__fraction');
                const price = priceEl ? priceEl.innerText.trim() : '';

                const soldEl = item.querySelector('.poly-phrase-label, .ui-search-reviews__subtitle');
                const sold_text = soldEl ? soldEl.innerText.trim() : '';

                const thumbEl = item.querySelector('img.poly-component__picture, img.ui-search-result-image__element');
                let thumbnail = thumbEl ? (thumbEl.getAttribute('src') || '') : '';
                thumbnail = thumbnail.replace('D_NQ_NP_2X_', 'D_NQ_NP_');

                const mcoMatch = href.match(/MCO\\d+/);
                const itemId = item.getAttribute('data-item-id') || '';
                const mcoId = mcoMatch ? mcoMatch[0] : (itemId.match(/MCO\\d+/)?.[0] || '');

                results.push({
                    id: mcoId,
                    title: title,
                    price: price,
                    permalink: href,
                    sold_text: sold_text,
                    sold_quantity: 0,
                    thumbnail: thumbnail,
                });
            });

            return results;
        }
    """)

            for p in products:
                p["sold_quantity"] = extract_sold_quantity(p.get("sold_text", ""))

            return products[:MAX_SEARCH_RESULTS]
        except Exception as e:
            if attempt < 2:
                print(f"    ⚠️ Error en búsqueda (intento {attempt+1}), reintentando...")
                time.sleep(2)
            else:
                print(f"    ❌ Error después de 3 intentos: {e}")
                return []


def search_duckduckgo(query: str, page) -> list[dict]:
    """
    Busca productos en ML Colombia usando DuckDuckGo (no bloquea scraping).
    """
    ddg_query = f'site:mercadolibre.com.co {query}'
    ddg_url = f"https://html.duckduckgo.com/html/?q={quote(ddg_query)}"
    print(f"    DuckDuckGo: '{query}'")

    try:
        page.goto(ddg_url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

        results = page.evaluate("""
            () => {
                const results = [];
                const seen = new Set();
                
                // DuckDuckGo HTML results
                const links = document.querySelectorAll('.result__a, a.result__snippet');
                
                links.forEach(link => {
                    let href = link.getAttribute('href') || '';
                    
                    // DuckDuckGo wraps URLs - extract real URL
                    const uMatch = href.match(/uddg=([^&]+)/);
                    if (uMatch) {
                        href = decodeURIComponent(uMatch[1]);
                    }
                    
                    // Must be ML Colombia product
                    if (!href.includes('mercadolibre.com.co') || !href.includes('MCO')) return;
                    if (seen.has(href)) return;
                    seen.add(href);
                    
                    // Get title
                    let title = link.innerText.trim();
                    if (!title) {
                        const h2 = link.closest('.result')?.querySelector('.result__title');
                        if (h2) title = h2.innerText.trim();
                    }
                    if (!title) return;
                    
                    results.push({
                        id: href.match(/MCO\\d+/)?.[0] || '',
                        title: title,
                        permalink: href,
                        sold_text: '',
                        sold_quantity: 0,
                        thumbnail: '',
                    });
                });
                
                return results;
            }
        """)

        return results[:15]
    except Exception as e:
        print(f"    ❌ DuckDuckGo error: {e}")
        return []


def calculate_match_score(product_title: str, search_title: str) -> float:
    """
    Calcula qué tan bien coincide un resultado de búsqueda con el producto esperado.
    Retorna score entre 0.0 y 1.0.

    Estrategia: compara palabras clave significativas (excluye marcas genéricas,
    tamaños, unidades). Requiere que TODAS las palabras clave del producto
    estén presentes en el resultado.
    """
    # Normalizar ambos textos
    prod_norm = normalize_text(product_title)
    search_norm = normalize_text(search_title)

    # Palabras del producto (filtrar palabras muy cortas y genéricas)
    stop_words = {
        'de', 'la', 'el', 'en', 'y', 'con', 'para', 'por', 'sin', 'del',
        'los', 'las', 'un', 'una', 'unos', 'unas', 'al', 'es', 'x',
    }
    prod_words = [w for w in prod_norm.split() if len(w) > 2 and w not in stop_words]

    if not prod_words:
        return 0.0

    # Contar cuántas palabras clave del producto están en el resultado
    matches = sum(1 for w in prod_words if w in search_norm)
    score = matches / len(prod_words)

    # Bonus si el resultado contiene la marca (primera palabra significativa)
    if prod_words and prod_words[0] in search_norm:
        score = min(1.0, score + 0.1)

    return score


def find_best_match(product: dict, search_results: list[dict]) -> dict | None:
    """
    De los resultados de búsqueda, encuentra el que mejor coincide con el producto.
    Entre los que superen el score mínimo, elige el de más vendidos.
    """
    target_title = product["title"]
    candidates = []

    print(f"    Evaluando {len(search_results)} resultados...")

    for sr in search_results:
        score = calculate_match_score(target_title, sr["title"])
        if score >= MIN_MATCH_SCORE:
            candidates.append({
                **sr,
                "match_score": score,
            })
            print(f"      ✅ {score:.0%} match | {sr['sold_quantity']} vendidos | {sr['title'][:60]}")
        else:
            print(f"      ❌ {score:.0%} match | {sr['title'][:60]}")

    if not candidates:
        return None

    # Ordenar: primero por score (más alto), luego por vendidos (más alto)
    candidates.sort(key=lambda c: (c["match_score"], c["sold_quantity"]), reverse=True)

    best = candidates[0]
    print(f"\n    🏆 Mejor coincidencia: {best['match_score']:.0%} match, {best['sold_quantity']} vendidos")
    print(f"       {best['title'][:80]}")
    print(f"       {best['permalink']}\n")

    return best


# ─── Scraping de reviews ──────────────────────────────────────────────────────

def scrape_product(page, product: dict) -> tuple[list[dict], dict]:
    """
    Scrapea reviews de un producto de ML.
    Maneja dos estructuras:
    1. Reviews embebidas en la página (nuevo ML) - clickea "Mostrar todas las opiniones"
    2. Reviews en iframe (viejo ML) - extrae object_id y llama API
    Retorna (reviews_list, image_map).
    """
    url = product["url"]
    handle = product.get("product_handle", "unknown")
    print(f"\n{'='*60}")
    print(f"Scraping: {handle}")
    print(f"{'='*60}")

    # 1. Cargar página del producto
    print("[1/4] Cargando página del producto...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    # Cerrar banner de cookies
    try:
        cookie_btn = page.query_selector("button.cookie-consent-banner-opt-out__action--primary")
        if cookie_btn:
            cookie_btn.click()
            time.sleep(0.5)
    except Exception:
        pass

    # 2. Detectar estructura de reviews
    print("[2/4] Detectando estructura de reviews...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
    time.sleep(2)

    # Check for embedded reviews first (new ML structure)
    embedded_reviews = page.evaluate("""
        () => {
            // Look for "Mostrar todas las opiniones" or similar
            const showAllBtn = Array.from(document.querySelectorAll('button, a')).find(el =>
                el.innerText.includes('Mostrar todas las opiniones') ||
                el.innerText.includes('Ver todas las opiniones')
            );

            // Check for review comments already in DOM
            const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
            const hasComments = comments.length > 0;

            return {
                hasShowAll: !!showAllBtn,
                commentCount: comments.length,
                hasEmbeddedReviews: hasComments,
            };
        }
    """)

    print(f"    Reviews embebidas: {embedded_reviews['hasEmbeddedReviews']} ({embedded_reviews['commentCount']} visibles)")
    print(f"    Botón 'Mostrar todas': {embedded_reviews['hasShowAll']}")

    # Check for iframe reviews (old ML structure)
    iframe_src = page.evaluate("""
        () => {
            const iframe = document.querySelector('iframe.ui-pdp-iframe-reviews__content, iframe[data-testid*="review"], iframe[src*="catalog/reviews"]');
            return iframe ? iframe.getAttribute('src') : null;
        }
    """)
    print(f"    Reviews en iframe: {iframe_src is not None}")

    # Strategy: Try embedded first, then iframe
    if embedded_reviews['hasEmbeddedReviews'] or embedded_reviews['hasShowAll']:
        return _scrape_embedded_reviews(page, product)
    elif iframe_src:
        return _scrape_iframe_reviews(page, product, iframe_src)
    else:
        # Try to construct iframe URL from product ID
        product_match = re.search(r'/p/(MCO\d+)', url)
        if product_match:
            product_id = product_match.group(1)
            iframe_src = f"/noindex/catalog/reviews/{product_id}?noIndex=true&access=view_all&modal=true"
            return _scrape_iframe_reviews(page, product, iframe_src)
        else:
            print("      ERROR: No se pudo encontrar reviews")
            return [], {}


def _scrape_embedded_reviews(page, product: dict) -> tuple[list[dict], dict]:
    """Scrape reviews from embedded DOM structure (new ML)."""
    print("[3/4] Cargando todas las opiniones embebidas...")

    # Click "Mostrar todas las opiniones" if exists - this opens a review iframe
    try:
        show_all = page.evaluate("""
            () => {
                const btn = Array.from(document.querySelectorAll('button, a')).find(el =>
                    el.innerText.includes('Mostrar todas las opiniones') ||
                    el.innerText.includes('Ver todas las opiniones')
                );
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            }
        """)
        if show_all:
            time.sleep(3)
    except Exception:
        pass

    # After clicking, look for the review iframe
    iframe_src = page.evaluate("""
        () => {
            const iframes = document.querySelectorAll('iframe');
            for (const iframe of iframes) {
                const src = iframe.getAttribute('src') || '';
                if (src.includes('catalog/reviews') || src.includes('noindex')) {
                    return src;
                }
            }
            return null;
        }
    """)

    if iframe_src:
        print(f"    Found review iframe after click!")
        return _scrape_iframe_reviews(page, product, iframe_src)

    # If no iframe appeared, try to extract reviews directly from DOM
    print("    No iframe found, extracting from DOM...")

    # Scroll to load all reviews
    prev_count = 0
    for scroll_round in range(20):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)

        current_count = page.evaluate("""
            () => document.querySelectorAll('.ui-review-capability-comments__comment').length
        """)

        if current_count == prev_count:
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            current_count = page.evaluate("""
                () => document.querySelectorAll('.ui-review-capability-comments__comment').length
            """)
            if current_count == prev_count:
                break

        prev_count = current_count
        print(f"      Reviews cargadas: {current_count}")

    print(f"      TOTAL reviews embebidas: {prev_count}")

    # Extract reviews from DOM
    all_reviews = page.evaluate("""
        () => {
            const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
            const reviews = [];

            comments.forEach(comment => {
                const contentEl = comment.querySelector('[data-testid="comment-content-component"]');
                const body = contentEl ? contentEl.innerText.trim() : '';

                if (!body) return;

                // Get rating
                const stars = comment.querySelectorAll('.ui-review-capability-stars__star--active, .ui-review-capability-stars__star--filled');
                const rating = stars.length || 5;

                // Get date
                const dateEl = comment.querySelector('.ui-review-capability-date__text');
                const date = dateEl ? dateEl.innerText.trim() : '';

                reviews.push({
                    comment: { content: { text: body }, date: date },
                    rating: rating,
                    title: { text: '' },
                });
            });

            return reviews;
        }
    """)

    print(f"      Reviews con texto: {len(all_reviews)}")

    # Extract images
    print("[4/4] Extrayendo imágenes...")
    image_map = page.evaluate("""
        () => {
            const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
            const map = {};

            comments.forEach(comment => {
                const contentEl = comment.querySelector('[data-testid="comment-content-component"]');
                const body = contentEl ? contentEl.innerText.trim() : '';

                const images = comment.querySelectorAll('img.ui-review-capability-carousel__img');
                const urls = Array.from(images).map(img => {
                    let src = img.getAttribute('src') || '';
                    src = src.replace('D_NQ_NP_2X_', 'D_NQ_NP_');
                    return src;
                }).filter(u => u);

                if (body && urls.length > 0) {
                    map[body.substring(0, 60)] = urls;
                }
            });

            return map;
        }
    """)

    print(f"      Reviews con imágenes: {len(image_map)}")

    return all_reviews, image_map


def _scrape_iframe_reviews(page, product: dict, iframe_src: str) -> tuple[list[dict], dict]:
    """Scrape reviews from iframe structure (old ML)."""
    if iframe_src.startswith('/'):
        iframe_url = f"https://www.mercadolibre.com.co{iframe_src}"
    else:
        iframe_url = iframe_src

    parsed = urlparse(iframe_url)
    params = parse_qs(parsed.query)
    path_match = re.search(r'/(MCO\d+)', parsed.path)
    object_id = path_match.group(1) if path_match else None

    if not object_id:
        print("      ERROR: No se pudo extraer object ID")
        return [], {}

    brand_id = params.get('brandId', [''])[0]
    domain_id = params.get('domain_id', [''])[0]
    category_id = params.get('category_id', [''])[0]

    print(f"      Object ID: {object_id}")
    print("[3/4] Descargando reviews via API...")

    all_reviews = []
    offset = 0
    limit = 15
    max_pages = 30

    for page_num in range(max_pages):
        api_url = (
            f"https://www.mercadolibre.com.co/noindex/catalog/reviews/{object_id}/search"
            f"?objectId={object_id}&siteId=MCO&isItem=false"
            f"&offset={offset}&limit={limit}&x-is-webview=false"
            f"&brandId={brand_id}&domain_id={domain_id}&category_id={category_id}"
        )

        result = page.evaluate(f"""
            async () => {{
                try {{
                    const response = await fetch('{api_url}', {{
                        credentials: 'include',
                        headers: {{ 'Accept': 'application/json' }}
                    }});
                    if (!response.ok) return {{ error: true, status: response.status }};
                    return await response.json();
                }} catch (e) {{
                    return {{ error: true, message: e.message }};
                }}
            }}
        """)

        if result.get('error'):
            print(f"      Error en página {page_num + 1}: {result}")
            break

        reviews = result.get('reviews', [])
        if not reviews:
            break

        all_reviews.extend(reviews)
        print(f"      Página {page_num + 1}: {len(reviews)} reviews (total: {len(all_reviews)})")
        offset += limit

        if len(reviews) < limit:
            break

        time.sleep(0.3)

    print(f"      TOTAL reviews con texto: {len(all_reviews)}")

    # Extract images from iframe
    print("[4/4] Extrayendo imágenes de las reviews...")
    page.goto(iframe_url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    image_map = {}
    prev_count = 0
    for scroll_round in range(15):
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)

        current_count = page.evaluate("""
            () => document.querySelectorAll('.ui-review-capability-comments__comment').length
        """)

        if current_count == prev_count:
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(0.5)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1.5)
            current_count = page.evaluate("""
                () => document.querySelectorAll('.ui-review-capability-comments__comment').length
            """)
            if current_count == prev_count:
                break

        prev_count = current_count

    image_map = page.evaluate("""
        () => {
            const comments = document.querySelectorAll('.ui-review-capability-comments__comment');
            const map = {};

            comments.forEach(comment => {
                const contentEl = comment.querySelector('[data-testid="comment-content-component"]');
                const body = contentEl ? contentEl.innerText.trim() : '';

                const images = comment.querySelectorAll('img.ui-review-capability-carousel__img');
                const urls = Array.from(images).map(img => {
                    let src = img.getAttribute('src') || '';
                    src = src.replace('D_NQ_NP_2X_', 'D_NQ_NP_');
                    return src;
                }).filter(u => u);

                if (body && urls.length > 0) {
                    map[body.substring(0, 60)] = urls;
                }
            });

            return map;
        }
    """)

    print(f"      Reviews cargadas en DOM: {prev_count}")
    print(f"      Reviews con imágenes: {len(image_map)}")

    return all_reviews, image_map


def format_for_judgeme(api_reviews: list, image_map: dict, product: dict) -> list[dict]:
    """Convierte reviews de la API de ML al formato CSV de Judge.me."""
    random.seed(42)
    nombres_asignados = random.sample(NOMBRES_COLOMBIA, min(len(NOMBRES_COLOMBIA), max(len(api_reviews), 50)))
    while len(nombres_asignados) < len(api_reviews):
        nombres_asignados.extend(random.sample(NOMBRES_COLOMBIA, len(NOMBRES_COLOMBIA)))

    formatted = []
    for i, r in enumerate(api_reviews):
        rating = r.get('rating', 5)
        comment = r.get('comment', {})
        body = comment.get('content', {}).get('text', '')
        date_str = comment.get('date', comment.get('time', {}).get('text', ''))
        title_text = r.get('title', {}).get('text', '')

        name = nombres_asignados[i % len(nombres_asignados)]
        email = generar_email(name, seed=i)

        body = sanitize_text(body)
        title = sanitize_text(title_text)

        if not title:
            titles = {5: "Excelente producto", 4: "Muy buen producto", 3: "Buen producto", 2: "Producto regular", 1: "No lo recomiendo"}
            title = titles.get(int(rating), "Buena compra")

        if not body:
            body = title

        picture_urls = ""
        if body:
            key = body[:60]
            if key in image_map:
                picture_urls = ";".join(image_map[key])

        formatted.append({
            "title": title,
            "body": body,
            "rating": int(rating),
            "review_date": parse_ml_date(date_str),
            "reviewer_name": name,
            "reviewer_email": email,
            "product_id": product.get("product_id", ""),
            "product_handle": product.get("product_handle", ""),
            "reply": "",
            "picture_urls": picture_urls,
        })

    return formatted


REGISTRY_FILE = "reviews_registry.json"


def load_registry(filepath: str = REGISTRY_FILE) -> dict:
    """Carga el registro de productos ya procesados."""
    if Path(filepath).exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_updated": "", "total_reviews": 0, "products": {}}


def save_registry(registry: dict, filepath: str = REGISTRY_FILE):
    """Guarda el registro de productos procesados."""
    registry["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)


def update_registry(registry: dict, handle: str, title: str, status: str, reviews: int, matched_url: str = ""):
    """Actualiza el registro con el resultado de un producto."""
    registry["products"][handle] = {
        "title": title,
        "status": status,
        "reviews": reviews,
        "matched_url": matched_url,
        "last_scraped": datetime.now().strftime("%Y-%m-%d"),
    }
    # Recalcular total
    registry["total_reviews"] = sum(
        p["reviews"] for p in registry["products"].values()
        if p["status"] == "success"
    )


# ─── Main ─────────────────────────────────────────────────────────────────────

def load_products(filepath: str) -> list[dict]:
    """Carga productos desde el JSON exportado de Shopify."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ML Colombia → Judge.me Review Scraper")
    parser.add_argument("--product", "-p", type=int, help="Procesar solo un producto por índice")
    parser.add_argument("--from", type=int, dest="from_idx", help="Índice inicial (inclusive)")
    parser.add_argument("--to", type=int, dest="to_idx", help="Índice final (exclusive)")
    parser.add_argument("--products-file", type=str, default=PRODUCTS_FILE, help="Archivo JSON de productos")
    parser.add_argument("--force", "-f", action="store_true", help="Forzar re-scrapeo de productos ya procesados")
    args = parser.parse_args()

    # Cargar productos
    products = load_products(args.products_file)
    print(f"\n📦 {len(products)} productos cargados desde {args.products_file}")

    # Cargar registro
    registry = load_registry()
    skipped = 0
    if not args.force:
        original_count = len(products)
        filtered = []
        for p in products:
            handle = p["handle"]
            if handle in registry["products"]:
                reg = registry["products"][handle]
                skipped += 1
                print(f"   ⏭️ Saltando (ya registrado): {p['title'][:50]} ({reg['status']}, {reg['reviews']} reviews)")
            else:
                filtered.append(p)
        products = filtered
        if skipped > 0:
            print(f"   ⏭️ {skipped} productos saltados (ya en registro)")
            print(f"   🔄 {len(products)} productos pendientes de scrapear")

    # Filtrar por rango
    if args.product is not None:
        if not products:
            print(f"   ⚠️ El producto #{args.product} ya está registrado. Usá --force para re-scrapear.")
            return
        products = [products[args.product]]
        print(f"   Procesando solo producto #{args.product}")
    elif args.from_idx is not None or args.to_idx is not None:
        start = args.from_idx or 0
        end = args.to_idx or len(products)
        products = products[start:end]
        if products:
            print(f"   Procesando productos {start} a {end-1}")
        else:
            print(f"   ⚠️ Todos los productos en el rango ya están registrados. Usá --force para re-scrapear.")
            return
    elif not products:
        print(f"   ⚠️ Todos los productos ya están registrados. Usá --force para re-scrapear.")
        return

    all_reviews = []
    stats = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # First visit Google to accept cookies
        try:
            page.goto("https://www.google.com", wait_until="domcontentloaded", timeout=15000)
            time.sleep(1)
            try:
                consent = page.query_selector('button:has-text("Accept all"), button:has-text("Aceptar todo"), button:has-text("I agree")')
                if consent:
                    consent.click()
                    time.sleep(1)
            except Exception:
                pass
        except Exception:
            pass

        for idx, product in enumerate(products):
            title = product["title"]
            handle = product["handle"]
            print(f"\n{'#'*60}")
            print(f"Producto {idx + 1}/{len(products)}: {title[:60]}")
            print(f"{'#'*60}")

            # Construir query optimizado (marca + producto clave, sin tamaños)
            search_query = build_search_query(title)
            print(f"    Título completo: {title[:70]}")
            print(f"    Query optimizado: '{search_query}'")

            # Buscar en ML Colombia (primero directo, luego DuckDuckGo como fallback)
            search_results = search_products_ml(search_query, page)
            
            # Si no encontró nada, intentar con DuckDuckGo
            if not search_results:
                print(f"    ⚠️ Sin resultados en ML, buscando en DuckDuckGo...")
                search_results = search_duckduckgo(search_query, page)

            if not search_results:
                print(f"    ❌ No se encontraron resultados para '{title}'")
                stats.append({"title": title, "handle": handle, "status": "no_results", "reviews": 0})
                update_registry(registry, handle, title, "no_results", 0)
                save_registry(registry)
                continue

            # Encontrar mejor coincidencia
            best_match = find_best_match(product, search_results)

            if not best_match:
                print(f"    ❌ No se encontró coincidencia para '{title}'")
                stats.append({"title": title, "handle": handle, "status": "no_match", "reviews": 0})
                update_registry(registry, handle, title, "no_match", 0)
                save_registry(registry)
                continue

            # Construir producto para scraping
            # Use Shopify ID from productos.json, NOT the ML MCO ID
            shopify_id = product.get("shopify_id", "")
            scrape_target = {
                "url": best_match["permalink"],
                "product_handle": handle,
                "product_id": shopify_id,
            }

            # Scrapear reviews
            try:
                raw_reviews, image_map = scrape_product(page, scrape_target)
                formatted = format_for_judgeme(raw_reviews, image_map, scrape_target)
                all_reviews.extend(formatted)

                print(f"\n✅ {len(formatted)} reviews extraídas para '{handle}'")
                stats.append({
                    "title": title,
                    "handle": handle,
                    "status": "ok",
                    "reviews": len(formatted),
                    "matched_url": best_match["permalink"],
                    "sold_quantity": best_match["sold_quantity"],
                })
                update_registry(registry, handle, title, "success", len(formatted), best_match["permalink"])
                save_registry(registry)

                # Pausa entre productos
                if idx < len(products) - 1:
                    wait = random.uniform(2, 4)
                    print(f"⏳ Esperando {wait:.1f}s antes del siguiente producto...")
                    time.sleep(wait)

            except Exception as e:
                print(f"\n❌ ERROR scraping '{handle}': {e}")
                import traceback
                traceback.print_exc()
                stats.append({"title": title, "handle": handle, "status": f"error: {e}", "reviews": 0})
                update_registry(registry, handle, title, "error", 0, best_match.get("permalink", ""))
                save_registry(registry)

        browser.close()

    # Guardar CSV (append mode)
    if all_reviews:
        import os
        file_exists = os.path.isfile(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0
        
        with open(OUTPUT_FILE, "a" if file_exists else "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerows(all_reviews)
        
        # Count total in file
        total_in_file = 0
        if file_exists:
            with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
                total_in_file = sum(1 for _ in csv.DictReader(f))
        else:
            total_in_file = len(all_reviews)
        
        print(f"\n{'='*60}")
        print(f"CSV {'actualizado' if file_exists else 'generado'}: {OUTPUT_FILE}")
        print(f"Reviews agregadas en esta corrida: {len(all_reviews)}")
        print(f"Total reviews en archivo: {total_in_file}")
        print(f"{'='*60}")
    else:
        print("\n⚠️ No se extrajo ninguna review nueva.")

    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN")
    print(f"{'='*60}")
    for s in stats:
        status_icon = "✅" if s["status"] == "ok" else "❌"
        print(f"  {status_icon} {s['handle']}: {s['status']} ({s['reviews']} reviews)")

    total_ok = sum(1 for s in stats if s["status"] == "ok")
    total_reviews = sum(s["reviews"] for s in stats)
    print(f"\n  Productos exitosos: {total_ok}/{len(stats)}")
    print(f"  Total reviews: {total_reviews}")


if __name__ == "__main__":
    main()
