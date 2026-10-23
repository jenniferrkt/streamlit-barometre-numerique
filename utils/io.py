"""Getting the data: download it once, keep a small copy, and load it for the app."""
 
import json
from pathlib import Path
 
import pandas as pd
import requests
 
import config as cfg
 
 
def fetch_and_cache(url, dest, *, force=False, chunk_size=1 << 20, timeout=60):
    """Download the file at ``url`` and save it as ``dest``, unless it is already there.
 
    The download goes to a temporary ``.part`` file first. It is renamed only when it is complete,
    so a download that stops halfway never leaves a broken file behind.
    """
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 0 and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    try:
        with requests.get(url, stream=True, timeout=timeout, allow_redirects=True) as resp:
            resp.raise_for_status()
            expected = int(resp.headers.get("Content-Length", 0))
            written = 0
            with open(part, "wb") as f:
                for block in resp.iter_content(chunk_size=chunk_size):
                    f.write(block)
                    written += len(block)
        if written == 0 or (expected and written != expected):
            raise IOError(f"Incomplete download: got {written} bytes, expected {expected or 'unknown'}")
        part.replace(dest)
    finally:
        part.unlink(missing_ok=True)
    return dest
 
 
def ensure_extract(*, force=False):
    """Return the small prepared data file. If it does not exist yet, download the source and build it."""
    if cfg.EXTRACT_PARQUET.exists() and cfg.ADOPTION_PARQUET.exists() and cfg.QUALITY_JSON.exists() and not force:
        return cfg.EXTRACT_PARQUET
    from utils.prep import build_extract  # imported here so this file stays light when the data is already prepared
 
    fetch_and_cache(cfg.DATA_URL, cfg.RAW_CSV)
    build_extract(cfg.RAW_CSV, cfg.EXTRACT_PARQUET, cfg.QUALITY_JSON)
    return cfg.EXTRACT_PARQUET
 
 
def load_extract():
    """Load the small prepared data and the quality report made from the full source file."""
    path = ensure_extract()
    extract = pd.read_parquet(path)
    report = json.loads(cfg.QUALITY_JSON.read_text(encoding="utf-8"))
    return extract, report
 
 
def load_adoption():
    """Load the long series: use of social networks from 2009 to 2022."""
    ensure_extract()
    return pd.read_parquet(cfg.ADOPTION_PARQUET)
 
 
def license_text():
    """The sentence that cites the source and its licence."""
    return (
        f"Data: {cfg.DATASET_TITLE}, {cfg.DATASET_PRODUCER}, via data.gouv.fr "
        f"({cfg.DATASET_PAGE}). Licence: {cfg.LICENSE_NAME} ({cfg.LICENSE_URL})."
    )
 