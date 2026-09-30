import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Configure UTF-8 output for Windows terminal support
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables from .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# MySQL Connection Configuration
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_DB = os.getenv("MYSQL_DB", "resilience_db")
ENABLE_SQLITE_FALLBACK = os.getenv("ENABLE_SQLITE_FALLBACK", "true").lower() == "true"

# Construct MySQL Database URL
MYSQL_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"

# Fallback SQLite DB path
SQLITE_PATH = os.path.join(BASE_DIR, "resilience.db")
SQLITE_URL = f"sqlite:///{SQLITE_PATH}"

def initialize_engine():
    """Attempts to connect via DATABASE_URL or MySQL/SQLite cleanly without blocking server import."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        elif db_url.startswith("mysql://") and "mysql+pymysql://" not in db_url:
            db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
        print("✅ Configured Cloud Database via DATABASE_URL with Connection Pooling")
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_recycle=1800,
            pool_pre_ping=False
        )
        return engine, "cloud_db"

    # If no DATABASE_URL, check if local MySQL is explicitly requested or fallback to SQLite
    if os.getenv("MYSQL_HOST") and os.getenv("MYSQL_HOST") != "localhost":
        try:
            engine = create_engine(MYSQL_URL, pool_recycle=3600, pool_pre_ping=True)
            return engine, "mysql"
        except Exception as e:
            print(f"⚠️ MySQL Connection failed ({e}). Falling back to SQLite...")

    print("ℹ️ Using local SQLite database engine...")
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    return engine, "sqlite"

engine, DB_TYPE = initialize_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
