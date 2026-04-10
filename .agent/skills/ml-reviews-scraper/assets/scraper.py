"""
Mercado Libre → Judge.me (Shopify) Review Scraper
==================================================
Extrae TODAS las reviews con texto de productos de ML
y genera un CSV compatible con la importación masiva de Judge.me.

Estrategia:
- Usa la API interna de ML: /noindex/catalog/reviews/{objectId}/search
- Paginación con offset/limit (max 15 por página)
- Se llama desde el contexto de la página del producto (mantiene cookies)
- Imágenes se extraen del DOM haciendo scroll progresivo

Nota: El total de "calificaciones" incluye ratings sin texto.
Solo se extraen reviews con comentario escrito.

Uso:
    python scraper.py "URL" "shopify-handle"
    python scraper.py "URL1" "handle1" "URL2" "handle2"
    python scraper.py "URL" "handle" -o output.csv
    python scraper.py "URL" "handle" --headless

Por defecto escribe un raw export nuevo en exports/raw/.
"""

import csv
import re
import sys
import time
import random
import argparse
import unicodedata
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from playwright.sync_api import sync_playwright

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_RAW_EXPORT_DIR = REPO_ROOT / "exports" / "raw"
DEFAULT_MANUAL_EXPORT_DIR = REPO_ROOT / "exports" / "manual"

FIELDNAMES = [
    "title", "body", "rating", "review_date", "reviewer_name",
    "reviewer_email", "product_id", "product_handle", "reply", "picture_urls",
]

MONTH_ES = {
    "ene": "01", "feb": "02", "mar": "03", "abr": "04",
    "may": "05", "jun": "06", "jul": "07", "ago": "08",
    "sep": "09", "oct": "10", "nov": "11", "dic": "12",
}


def normalize_picture_urls(value) -> str:
    if not value:
        return ""

    if isinstance(value, str):
        candidates = re.split(r"[,;\n]+", value)
    else:
        candidates = list(value)

    urls = []
    seen = set()
    for candidate in candidates:
        url = str(candidate).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) == 5:
            break

    return ",".join(urls)


def sanitize_export_segment(value: str) -> str:
    segment = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    return segment.strip(".-_") or "product"


def build_raw_output_path(handles: list[str], now: datetime | None = None) -> Path:
    now = now or datetime.utcnow()
    timestamp = now.strftime("%Y%m%dT%H%M%S") + f"-{now.microsecond // 1000:03d}Z"
    handle_segment = "-".join(sanitize_export_segment(handle) for handle in handles[:4] if handle)
    if not handle_segment:
        handle_segment = "reviews"
    return DEFAULT_RAW_EXPORT_DIR / f"{timestamp}__{handle_segment}.csv"


def ensure_export_workspace() -> None:
    DEFAULT_RAW_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_MANUAL_EXPORT_DIR.mkdir(parents=True, exist_ok=True)


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
        estrategias.append(f"{primero}.{tercero}")
    if len(partes) >= 1:
        primero = re.sub(r'[^a-z]', '', partes[0])
        estrategias.append(f"{primero}{random.randint(100, 9999)}")
        estrategias.append(f"{primero}.{random.randint(10, 99)}")
    email_base = random.choice(estrategias)
    return f"{email_base}@{dominio}"


def scrape_product(page, product: dict) -> tuple:
    """Scrapea reviews de un producto de ML via API + DOM."""
    url = product["url"]
    print(f"\n{'='*60}")
    print(f"Producto: {product['product_handle']}")
    print(f"{'='*60}")

    # 1. Cargar página del producto
    print("[1/4] Cargando página del producto...")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(3)

    try:
        cookie_btn = page.query_selector("button.cookie-consent-banner-opt-out__action--primary")
        if cookie_btn:
            cookie_btn.click()
            time.sleep(0.5)
    except Exception:
        pass

    total_text = "desconocido"
    try:
        total_el = page.query_selector('[class*="rating__label"]')
        if total_el:
            total_text = total_el.inner_text()
            print(f"      Total calificaciones: {total_text}")
    except Exception:
        pass

    # 2. Extraer object_id del iframe de reviews
    print("[2/4] Buscando reviews...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
    time.sleep(2)

    iframe_src = page.evaluate("""
        () => {
            const iframe = document.querySelector('iframe.ui-pdp-iframe-reviews__content, iframe[data-testid*="review"], iframe[src*="catalog/reviews"]');
            return iframe ? iframe.getAttribute('src') : null;
        }
    """)

    if not iframe_src:
        show_more = page.query_selector('.show-more-click, [data-testid="see-more"]')
        if show_more:
            show_more.click()
            time.sleep(3)
            iframe_src = page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe.ui-pdp-iframe-reviews__content, iframe[data-testid*="review"], iframe[src*="catalog/reviews"]');
                    return iframe ? iframe.getAttribute('src') : null;
                }
            """)

    if not iframe_src:
        product_match = re.search(r'/p/(MCO\d+)', url)
        if product_match:
            product_id = product_match.group(1)
            iframe_src = f"/noindex/catalog/reviews/{product_id}?noIndex=true&access=view_all&modal=true"
        else:
            print("      ERROR: No se pudo encontrar reviews")
            return [], {}

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

    # 3. Llamar API paginada desde el contexto de la página (mantiene cookies)
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

    # 4. Extraer imágenes del DOM
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
            if key in image_map and image_map[key]:
                picture_urls = normalize_picture_urls(image_map[key])

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


def main():
    parser = argparse.ArgumentParser(description="Mercado Libre → Judge.me Review Scraper")
    parser.add_argument("products", nargs="+", help="URLs and handles: url1 handle1 [url2 handle2 ...]")
    parser.add_argument("-o", "--output", default=None, help="Output CSV file (default: timestamped CSV in exports/raw/)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()

    # Parse products: pairs of url + handle
    products = []
    items = args.products
    for i in range(0, len(items), 2):
        url = items[i]
        handle = items[i + 1] if i + 1 < len(items) else url.split('/')[-1].split('?')[0]
        products.append({"url": url, "product_handle": handle, "product_id": ""})

    ensure_export_workspace()

    all_reviews = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for product in products:
            try:
                raw, image_map = scrape_product(page, product)
                formatted = format_for_judgeme(raw, image_map, product)
                all_reviews.extend(formatted)
                print(f"\nOK: {len(formatted)} reviews para '{product['product_handle']}'")
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"\nERROR: {e}")
                import traceback
                traceback.print_exc()

        browser.close()

    output_file = Path(args.output).expanduser() if args.output else build_raw_output_path([product["product_handle"] for product in products])
    if all_reviews:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(all_reviews)
        print(f"\n{'='*60}")
        print(f"CSV generado: {output_file}")
        print(f"Total reviews: {len(all_reviews)}")
        print(f"{'='*60}")
    else:
        print("\nNo se extrajo ninguna review.")


if __name__ == "__main__":
    main()
