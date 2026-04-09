import argparse
import json, re, unicodedata, openpyxl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCTS = BASE_DIR / 'productos.json'
DEFAULT_EXCEL = BASE_DIR / 'Shopify_Publicaciones_Exportación_0404221023.xlsx'

def to_handle(title):
    text = title.lower().strip()
    text = unicodedata.normalize('NFKD', text)
    text = ''.join(c for c in text if not unicodedata.combining(c))
    text = text.replace('&', 'and')
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')

def parse_args():
    parser = argparse.ArgumentParser(description='Investigate Shopify product ID mismatches.')
    parser.add_argument('--productos', default=str(DEFAULT_PRODUCTS), help=f'Path to productos.json (default: {DEFAULT_PRODUCTS})')
    parser.add_argument('--excel', default=str(DEFAULT_EXCEL), help=f'Path to the Excel export (default: {DEFAULT_EXCEL})')
    return parser.parse_args()


def main():
    args = parse_args()

    with open(Path(args.productos).expanduser(), 'r', encoding='utf-8') as f:
        products = json.load(f)

    wb = openpyxl.load_workbook(Path(args.excel).expanduser(), data_only=True)
    ws = wb.active

    excel_products = {}
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
        pub_id = str(row[1]) if row[1] else ''
        title = row[2] if row[2] else ''
        excel_products[pub_id] = title

    # The 5 WRONG products
    wrong_ids = ['9266538217731', '9266537988355', '9250916696323', '9266537627907', '9268750090499']

    print('=' * 120)
    print('ANALYSIS OF 5 PRODUCTS WITH WRONG IDs')
    print('=' * 120)

    for p in products:
        if p['shopify_id'] in wrong_ids:
            expected_handle = to_handle(p['title'])
            actual_handle = p['handle']
            handle_match = 'MATCH' if expected_handle == actual_handle else 'MISMATCH'

            excel_title = excel_products.get(p['shopify_id'], 'NOT FOUND IN EXCEL')

            print(f'\nTitle: {p["title"]}')
            print(f'  Shopify ID (productos.json): {p["shopify_id"]}')
            print(f'  Handle (productos.json):     {actual_handle}')
            print(f'  Handle (expected):           {expected_handle}')
            print(f'  Handle match: {handle_match}')
            print(f'  In Excel (ID={p["shopify_id"]}): {excel_title}')
            print()

    # Now let's also check: do the 5 wrong IDs exist in the Excel?
    print('\n' + '=' * 120)
    print('DO THE 5 WRONG IDs EXIST IN THE EXCEL?')
    print('=' * 120)
    for wid in wrong_ids:
        title = excel_products.get(wid, 'NOT FOUND')
        print(f'  ID {wid}: {title[:80] if title != "NOT FOUND" else title}')

    # Check if the 10 correct IDs also match
    correct_ids = ['9135157051651', '9135157248259', '9135156691203', '9135151644931', '9135152300291',
                   '9135156625667', '9135155773699', '9135156297987', '9135156822275', '9135157281027']

    print('\n' + '=' * 120)
    print('DO THE 10 CORRECT IDs EXIST IN THE EXCEL?')
    print('=' * 120)
    for cid in correct_ids:
        title = excel_products.get(cid, 'NOT FOUND')
        print(f'  ID {cid}: {title[:80] if title != "NOT FOUND" else title}')

    # Now let's check if the wrong IDs are NEWER products not in the original export
    print('\n' + '=' * 120)
    print('ALL PRODUCTS IN productos.json NOT IN EXCEL')
    print('=' * 120)
    excel_ids = set(excel_products.keys())
    json_ids = set(p['shopify_id'] for p in products)
    missing_from_excel = json_ids - excel_ids
    for mid in sorted(missing_from_excel):
        p = next(x for x in products if x['shopify_id'] == mid)
        print(f'  ID {mid}: {p["title"][:80]}')

    # And products in Excel not in JSON
    missing_from_json = excel_ids - json_ids
    if missing_from_json:
        print('\nProducts in Excel but NOT in productos.json:')
        for mid in sorted(missing_from_json):
            print(f'  ID {mid}: {excel_products[mid][:80]}')


if __name__ == '__main__':
    main()
