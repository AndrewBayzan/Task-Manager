from dotenv import load_dotenv
import os

load_dotenv(".env.neon")

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_PORT = os.getenv("DB_PORT")
DB_HOST = os.getenv("DB_HOST")

NEONDB_URL = os.getenv("NEONDB_URL")

if NEONDB_URL:
    DB_URL = NEONDB_URL
else:
    missing_db_settings = [
        name
        for name, value in (
            ("DB_NAME", DB_NAME),
            ("DB_USER", DB_USER),
            ("DB_PASS", DB_PASS),
            ("DB_PORT", DB_PORT),
            ("DB_HOST", DB_HOST),
        )
        if not value
    ]
    if missing_db_settings:
        raise RuntimeError(
            "Set NEONDB_URL or configure local PostgreSQL with: "
            + ", ".join(missing_db_settings)
        )

    DB_URL = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )