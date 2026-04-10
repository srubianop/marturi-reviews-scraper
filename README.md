# MARTURI Reviews Scraper

Scrapea **todas las reviews** de productos de Mercado Libre y las exporta como un CSV compatible con la importación masiva de **Judge.me** para Shopify.

## Archivo base

- `data/productos.json` — mapeo de productos/handles a Shopify IDs
- `data/reviews_registry.json` — registro persistente de ejecuciones del scraper
- `data/reviews_judgeme_template.csv` — plantilla/sample header-only para arrancar importaciones o copiar estructura
- `data/legacy/` — CSVs históricos preservados por compatibilidad
- `exports/raw/` — landing zone ignorada por git para exports crudos timestamped
- `exports/manual/` — landing zone ignorada por git para suplementos manuales Judge.me-compatible
- `reviews_judgeme.csv` — bundle final consolidado para importación downstream
- `scripts/search/` — helpers de investigación y chequeo de Excel
- `scripts/debug/` — helpers de inspección/debug puntuales

## Características

- **API interna de ML** — Usa el endpoint `/noindex/catalog/reviews/{objectId}/search` para extraer texto, ratings y fechas de forma rápida y confiable
- **Extracción de imágenes** — Hace scroll progresivo en el DOM para capturar URLs de fotos de productos compartidas por compradores
- **Nombres colombianos realistas** — Asigna nombres y apellidos colombianos auténticos en lugar de "Cliente verificado"
- **Emails realistas** — Genera correos Gmail, Hotmail, Outlook, Yahoo, etc. relacionados con cada nombre
- **Encoding correcto** — CSV con BOM UTF-8 para que Excel abra acentos y ñ sin problemas
- **Multi-producto** — Scrapea varios productos en una sola ejecución

## Instalación

```bash
pip install playwright
playwright install chromium
```

## Uso

### Un producto

```bash
python scraper.py "https://www.mercadolibre.com.co/producto/p/MCO12345678" "mi-producto-handle"
```

### Varios productos

```bash
python scraper.py \
  "https://www.mercadolibre.com.co/prod1/p/MCO111" "producto-uno" \
  "https://www.mercadolibre.com.co/prod2/p/MCO222" "producto-dos"
```

### Output personalizado

```bash
python scraper.py "URL" "handle" -o mis_reviews.csv
```

### Flujo recomendado

El scraper ahora escribe por defecto un CSV nuevo en `exports/raw/` con nombre timestamped.
Para generar el bundle final compatible con Judge.me:

```bash
python scripts/consolidate_reviews.py
```

La consolidación usa como referencia `data/reviews_judgeme_template.csv` y toma inputs crudos desde `exports/raw/`.

Opcionalmente podés pasar inputs explícitos:

```bash
python scripts/consolidate_reviews.py exports/raw/20260409T221530-241Z__mi-producto.csv exports/manual/extra.csv
```

Herramientas de inspección:

```bash
python scripts/search/investigate.py --help
python scripts/search/check_excel.py --help
python scripts/debug/debug_reviews.py
python scripts/debug/extract_catalog_id.py
python scripts/debug/find_product.py
python scripts/debug/search_product.py
```

### Modo headless (servidores)

```bash
python scraper.py "URL" "handle" --headless
```

## Formato del CSV

El archivo generado es compatible con **Judge.me Direct Import**:

| Columna | Descripción |
|---------|-------------|
| `title` | Título del review |
| `body` | Texto del review |
| `rating` | 1-5 estrellas |
| `review_date` | `YYYY-MM-DD HH:MM:SS UTC` |
| `reviewer_name` | Nombre colombiano realista |
| `reviewer_email` | Email realista (gmail, hotmail, etc.) |
| `product_id` | ID del producto (opcional) |
| `product_handle` | Slug del producto en Shopify |
| `reply` | Respuesta del vendedor (vacío) |
| `picture_urls` | Hasta 5 URLs de imágenes por review, separadas por `,` |

## CSV de suplementos manuales

Los archivos en `exports/manual/` deben usar exactamente las mismas columnas Judge.me:

`title, body, rating, review_date, reviewer_name, reviewer_email, product_id, product_handle, reply, picture_urls`

`picture_urls` también debe ir separado por `,` y limitado a 5 URLs.

## Cómo funciona

```
1. Carga la página del producto → establece sesión/cookies
2. Extrae el object_id del iframe de reviews
3. Llama a la API paginada (max 15 por página) desde el contexto del navegador
4. Navega al iframe → scroll progresivo → extrae URLs de imágenes del DOM
5. Matchea imágenes con reviews por texto
6. Asigna nombres colombianos + emails realistas
7. Genera CSV con encoding utf-8-sig (BOM)
```

## Notas técnicas

- La API de ML tiene un límite de **15 reviews por página** (50 devuelve error 400)
- Las llamadas a la API deben hacerse desde el contexto de la página del producto (las cookies son necesarias)
- Las imágenes NO están en la API — se extraen del DOM haciendo scroll progresivo
- Las URLs de thumbnail se convierten a tamaño completo reemplazando `D_NQ_NP_2X_` por `D_NQ_NP_`

## Licencia

Apache-2.0
