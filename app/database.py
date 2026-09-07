import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to MySQL as requested
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "irsh123")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "salsabeel_db")

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}")

try:
    import pymysql
    # Automatically create the database if it doesn't exist yet
    init_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
    with init_conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;")
    init_conn.close()

    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection
    with engine.connect() as conn:
        print("Successfully connected to MySQL.")
except Exception as e:
    print(f"Failed to connect to MySQL: {e}")
    print("Falling back to SQLite for demonstration purposes so the app can run immediately.")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./salsabeel.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
