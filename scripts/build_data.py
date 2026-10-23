"""Download the Baromètre du numérique file and build the small data file used by the app.
 
How to use it (from the main project folder):
 
    python scripts/build_data.py                 # download if needed, then build
    python scripts/build_data.py --csv PATH      # use a CSV file you already have
    python scripts/build_data.py --force         # download again and rebuild
 
The big source file (about 256 MB) goes to data/raw/ and is not saved in git. The small data file
(data/barometre_extract_2023_2025.parquet) and the quality report (data/quality_report.json)
are light, so they are kept with the code.
"""
import argparse
import sys
from pathlib import Path
 
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
 
import config as cfg  # noqa: E402
from utils.io import fetch_and_cache  # noqa: E402
from utils.prep import build_extract  # noqa: E402
 
 
def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", type=Path, help="use this local CSV instead of downloading")
    parser.add_argument("--url", default=cfg.DATA_URL, help="source URL (default: data.gouv.fr resource)")
    parser.add_argument("--force", action="store_true", help="re-download even if cached")
    args = parser.parse_args()
 
    raw = args.csv or fetch_and_cache(args.url, cfg.RAW_CSV, force=args.force)
    print(f"Source file: {raw} ({Path(raw).stat().st_size / 1e6:.1f} MB)")
    report = build_extract(raw, cfg.EXTRACT_PARQUET, cfg.QUALITY_JSON)
    r, e = report["raw"], report["extract"]
    print(f"Raw:     {r['rows']:,} rows x {r['columns']:,} columns, years {r['years'][0]}-{r['years'][-1]}"
          f" (no survey in {r['years_without_wave']})")
    print(f"Extract: {e['rows']:,} rows x {e['columns']} columns, years {e['years']} -> {cfg.EXTRACT_PARQUET}")
    print(f"Long series: {report['adoption']['rows']:,} rows, years {report['adoption']['years']} -> {cfg.ADOPTION_PARQUET}")
    print(f"Report:  {cfg.QUALITY_JSON}")
 
 
if __name__ == "__main__":
    main()
 