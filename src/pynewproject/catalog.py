"""Template catalog fetching and caching."""

import importlib.resources
import json
import os
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

# Override via env var for local development or CI:
#   PYNEWPROJECT_CATALOG_URL=file:///path/to/catalog.json
#   PYNEWPROJECT_CATALOG_URL=https://raw.githubusercontent.com/.../catalog.json
CATALOG_URL = os.environ.get(
    "PYNEWPROJECT_CATALOG_URL",
    "https://raw.githubusercontent.com/ericsonj/pymaketool-templates/refs/heads/master/catalog.json",
)

CACHE_DIR = Path.home() / ".cache" / "pynewproject"
CACHE_FILE = CACHE_DIR / "catalog.json"
CACHE_TTL = 3600  # 1 hour

_PROCESS_CACHE: dict | None = None  # in-process singleton, reset on refresh


def _bundled_catalog() -> dict:
    """Return the catalog.json that ships inside this package."""
    data = (importlib.resources.files("pynewproject") / "catalog.json").read_text()
    return json.loads(data)


def fetch_catalog(refresh: bool = False) -> dict:
    """Return the template catalog.

    Resolution order:
    1. In-process singleton (same Python process, unless *refresh* is True)
    2. Fresh local cache (unless *refresh* is True)
    3. Remote URL (``PYNEWPROJECT_CATALOG_URL`` or default GitHub raw URL)
    4. Stale local cache (if remote fails)
    5. Bundled catalog shipped with this package (offline / repo not yet live)
    """
    global _PROCESS_CACHE
    if not refresh and _PROCESS_CACHE is not None:
        return _PROCESS_CACHE

    if not refresh and CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime
        if age < CACHE_TTL:
            _PROCESS_CACHE = json.loads(CACHE_FILE.read_text())
            return _PROCESS_CACHE

    url = CATALOG_URL

    # Support local file paths via file:// or plain filesystem path
    if url.startswith("file://"):
        _PROCESS_CACHE = json.loads(Path(url[7:]).read_text())
        return _PROCESS_CACHE

    if not url.startswith(("http://", "https://")):
        # Treat as a plain filesystem path (e.g. set via env var to a local catalog.json)
        _PROCESS_CACHE = json.loads(Path(url).read_text())
        return _PROCESS_CACHE

    try:
        req = Request(url, headers={"User-Agent": "pynewproject"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=2))
        _PROCESS_CACHE = data
        return _PROCESS_CACHE
    except URLError as exc:
        if CACHE_FILE.exists():
            print(f"[warning] Could not reach catalog ({exc}); using cached version.")
            _PROCESS_CACHE = json.loads(CACHE_FILE.read_text())
            return _PROCESS_CACHE
        print(
            f"[warning] Could not reach catalog ({exc}); using bundled fallback.\n"
            f"          Push https://github.com/ericsonj/pymaketool-templates to make "
            f"'pynewproject new' work."
        )
        _PROCESS_CACHE = _bundled_catalog()
        return _PROCESS_CACHE


def find_template(catalog: dict, name: str) -> dict | None:
    """Return the catalog entry for *name* (case-insensitive), or None."""
    for tmpl in catalog.get("templates", []):
        if tmpl["name"].lower() == name.lower():
            return tmpl
    return None
