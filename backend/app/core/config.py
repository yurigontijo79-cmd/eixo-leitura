from os import getenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "eixo_leitura.db"

# Opções: mock | real | mixed
CATALOG_SOURCE = getenv("EIXO_CATALOG_SOURCE", "mixed").strip().lower() or "mixed"

GOOGLE_BOOKS_API_KEY = getenv("GOOGLE_BOOKS_API_KEY", "").strip() or None
OPENLIBRARY_USER_AGENT = (
    getenv("OPENLIBRARY_USER_AGENT", "EIXOLeituraCatalogBot/0.1 (+local-ingest)").strip()
    or "EIXOLeituraCatalogBot/0.1 (+local-ingest)"
)
INGEST_TIMEOUT_SECONDS = float(getenv("INGEST_TIMEOUT_SECONDS", "20"))
GOOGLE_BOOKS_RETRY_MAX = int(getenv("GOOGLE_BOOKS_RETRY_MAX", "2"))
GOOGLE_BOOKS_BACKOFF_SECONDS = float(getenv("GOOGLE_BOOKS_BACKOFF_SECONDS", "1.5"))
OPENLIBRARY_THROTTLE_SECONDS = float(getenv("OPENLIBRARY_THROTTLE_SECONDS", "0.4"))
