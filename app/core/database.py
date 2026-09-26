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
    """Attempts to connect via DATABASE_URL or MySQL. If unreachable, falls back to SQLite smoothly."""
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        elif db_url.startswith("mysql://") and "mysql+pymysql://" not in db_url:
            db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)
        try:
            print("Connecting to cloud database via DATABASE_URL...")
            engine = create_engine(db_url, pool_recycle=3600, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Successfully connected to Cloud Database via DATABASE_URL!")
            return engine, "cloud_db"
        except Exception as e:
            print(f"⚠️ Cloud DATABASE_URL connection failed ({e}). Proceeding to MySQL/SQLite fallback...")

    try:
        # Create MySQL engine without database name first to auto-create database if missing
        admin_url = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}"
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
        admin_engine.dispose()

        # Connect to target MySQL database
        engine = create_engine(MYSQL_URL, pool_recycle=3600, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✅ Successfully connected to MySQL Database: [{MYSQL_DB}@{MYSQL_HOST}:{MYSQL_PORT}]")
        return engine, "mysql"
    except Exception as e:
        if ENABLE_SQLITE_FALLBACK:
            print(f"⚠️ MySQL Connection failed ({e}). Falling back to local SQLite database...")
            engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
            return engine, "sqlite"
        else:
            raise e

engine, DB_TYPE = initialize_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
