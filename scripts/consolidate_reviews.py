"""Consolidate raw and manual Judge.me CSV exports into one bundle."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_TEMPLATE = DATA_DIR / "reviews_judgeme_template.csv"
DEFAULT_RAW_DIR = REPO_ROOT / "exports" / "raw"
DEFAULT_MANUAL_DIR = REPO_ROOT / "exports" / "manual"
DEFAULT_OUTPUT = REPO_ROOT / "reviews_judgeme.csv"

FIELDNAMES = [
    "title",
    "body",
    "rating",
    "review_date",
    "reviewer_name",
    "reviewer_email",
    "product_id",
    "product_handle",
    "reply",
    "picture_urls",
]


def normalize_picture_urls(value) -> str:
    if not value:
        return ""

    if isinstance(value, str):
        parts = value.replace("\n", ",").replace(";", ",").split(",")
    else:
        parts = list(value)

    urls = []
    seen = set()
    for part in parts:
        url = str(part).strip()
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
        if len(urls) == 5:
            break
    return ",".join(urls)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge raw exports and manual Judge.me supplement CSVs into reviews_judgeme.csv using the data/ template reference"
    )
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help=f"Judge.me template/header reference (default: {DEFAULT_TEMPLATE})",
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Optional raw CSV inputs to merge. If omitted, uses exports/raw/*.csv",
    )
    parser.add_argument("--raw-dir", default=str(DEFAULT_RAW_DIR), help=f"Raw export directory (default: {DEFAULT_RAW_DIR})")
    parser.add_argument("--manual-dir", default=str(DEFAULT_MANUAL_DIR), help=f"Manual supplement directory (default: {DEFAULT_MANUAL_DIR})")
    parser.add_argument("-o", "--output", default=str(DEFAULT_OUTPUT), help=f"Final CSV path (default: {DEFAULT_OUTPUT})")
    return parser.parse_args()


def is_valid_header(fieldnames: list[str] | None) -> bool:
    if not fieldnames:
        return False
    normalized = [name.strip() for name in fieldnames]
    return normalized == FIELDNAMES


def read_judgeme_csv(path: Path, *, source_kind: str, strict: bool) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not is_valid_header(reader.fieldnames):
                message = (
                    f"WARNING: skipping {source_kind} file with invalid Judge.me header: {path}"
                )
                print(message, file=sys.stderr)
                if strict:
                    raise ValueError(message)
                return []

            rows: list[dict[str, str]] = []
            for row in reader:
                normalized = {field: (row.get(field, "") or "") for field in FIELDNAMES}
                normalized["picture_urls"] = normalize_picture_urls(normalized["picture_urls"])
                rows.append(normalized)
            return rows
    except FileNotFoundError:
        message = f"WARNING: missing {source_kind} file: {path}"
        print(message, file=sys.stderr)
        if strict:
            raise
        return []
    except Exception as exc:
        message = f"WARNING: skipping {source_kind} file {path}: {exc}"
        print(message, file=sys.stderr)
        if strict:
            raise
        return []


def collect_files(raw_dir: Path, manual_dir: Path, inputs: list[str]) -> tuple[list[Path], list[Path]]:
    raw_files: list[Path]
    if inputs:
        raw_files = [Path(item).expanduser() for item in inputs]
    else:
        raw_files = sorted(raw_dir.glob("*.csv"))

    manual_files = sorted(manual_dir.glob("*.csv"))
    return raw_files, manual_files


def handle_key(row: dict[str, str], source_path: Path) -> str:
    handle = (row.get("product_handle") or "").strip()
    return handle or source_path.stem


def collect_raw_rows(raw_files: list[Path]) -> list[dict[str, str]]:
    latest_rows_by_handle: dict[str, tuple[float, Path, list[dict[str, str]]]] = {}

    for raw_file in raw_files:
        rows = read_judgeme_csv(raw_file, source_kind="raw", strict=False)
        if not rows:
            continue

        try:
            source_mtime = raw_file.stat().st_mtime
        except FileNotFoundError:
            continue

        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[handle_key(row, raw_file)].append(row)

        for handle, handle_rows in grouped.items():
            current = latest_rows_by_handle.get(handle)
            if current is None or source_mtime >= current[0]:
                latest_rows_by_handle[handle] = (source_mtime, raw_file, handle_rows)

    collected: list[dict[str, str]] = []
    for _, _, handle_rows in sorted(latest_rows_by_handle.values(), key=lambda item: (item[0], str(item[1]))):
        collected.extend(handle_rows)
    return collected


def collect_manual_rows(manual_files: list[Path]) -> list[dict[str, str]]:
    collected: list[dict[str, str]] = []
    for manual_file in manual_files:
        collected.extend(read_judgeme_csv(manual_file, source_kind="manual supplement", strict=False))
    return collected


def write_output(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    template_path = Path(args.template).expanduser()
    raw_dir = Path(args.raw_dir).expanduser()
    manual_dir = Path(args.manual_dir).expanduser()
    output_path = Path(args.output).expanduser()

    # Validate the template reference if present; the file is header-only.
    read_judgeme_csv(template_path, source_kind="Judge.me template", strict=False)

    raw_files, manual_files = collect_files(raw_dir, manual_dir, args.inputs)
    raw_rows = collect_raw_rows(raw_files)
    manual_rows = collect_manual_rows(manual_files)
    final_rows = raw_rows + manual_rows

    if not final_rows:
        print("No valid Judge.me rows were found to consolidate.", file=sys.stderr)
        return 1

    write_output(final_rows, output_path)

    print(f"Wrote {len(final_rows)} rows to {output_path}")
    print(f"  Raw rows: {len(raw_rows)}")
    print(f"  Manual rows: {len(manual_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
