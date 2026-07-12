import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Default to MySQL as requested
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:irsh123@localhost/salsabeel_db")

try:
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
