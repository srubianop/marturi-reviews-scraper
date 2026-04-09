# MARTURI Reviews Scraper

Scrapea **todas las reviews** de productos de Mercado Libre y las exporta como un CSV compatible con la importación masiva de **Judge.me** para Shopify.

## Archivo base

- `reviews_judgeme_template.csv` — plantilla/sample header-only para arrancar importaciones o copiar estructura
- `reviews_judgeme.csv` — salida generada por defecto por el scraper

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
| `picture_urls` | URLs de imágenes separadas por `;` |

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
