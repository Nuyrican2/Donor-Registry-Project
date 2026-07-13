"""Import the two CSV exports from the command line.

Usage:
    python scripts/import_csv.py data/donors.csv data/products.csv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.services.importer import import_donors, import_products


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    donors_csv, products_csv = sys.argv[1], sys.argv[2]
    app = create_app()
    with app.app_context():
        result = import_donors(donors_csv)
        print(f"Donors:   {result['created']} created, {result['updated']} updated")
        result = import_products(products_csv)
        print(f"Products: {result['created']} created, {result['updated']} updated")
        if result["skipped"]:
            print(f"Skipped (no matching donor): {', '.join(result['skipped'])}")


if __name__ == "__main__":
    main()
