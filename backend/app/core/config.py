from os import getenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "eixo_leitura.db"

# Opções: mock | real | mixed
CATALOG_SOURCE = getenv("EIXO_CATALOG_SOURCE", "mixed").strip().lower() or "mixed"
