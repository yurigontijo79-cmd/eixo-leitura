from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "eixo_leitura.db"
