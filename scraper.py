"""Public CLI entrypoint for the Mercado Libre reviews scraper.

Delegates to the implementation that writes timestamped raw exports by default.
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


IMPL_PATH = Path(__file__).resolve().parent / ".agent" / "skills" / "ml-reviews-scraper" / "assets" / "scraper.py"


def main() -> None:
    spec = spec_from_file_location("ml_reviews_scraper_impl", IMPL_PATH)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"Implementation not found: {IMPL_PATH}")

    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    raise SystemExit(main())
