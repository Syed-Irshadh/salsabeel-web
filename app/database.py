import os
import re
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

IS_VERCEL = bool(os.getenv("VERCEL"))

# Production Supabase PostgreSQL connection string (direct fallback so Vercel always connects)
SUPABASE_PROD_URL = "postgresql://postgres.mpjivtjqophlgqauhizk:Irshadh%402006@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require"

raw_db_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
# If DATABASE_URL is not set, empty, or points to old camel-yacht instead of mpjivtjqophlgqauhizk
if not raw_db_url or not raw_db_url.strip() or "mpjivtjqophlgqauhizk" not in raw_db_url:
    raw_db_url = SUPABASE_PROD_URL

engine = None

# 1. If DATABASE_URL is explicitly set (e.g. from Vercel / Cloud DB)
if raw_db_url:
    db_url = raw_db_url.strip()
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    elif db_url.startswith("mysql://") and not db_url.startswith("mysql+pymysql://"):
        db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

    # Safely handle special characters (e.g. @) in the database password
    m = re.match(r'^(?P<scheme>[^:]+://)(?P<user>[^:]+):(?P<password>.+)@(?P<rest>[^@]+)$', db_url)
    if m:
        scheme, user, pwd, rest = m.group('scheme'), m.group('user'), m.group('password'), m.group('rest')
        if "@" in pwd:
            db_url = f"{scheme}{user}:{quote_plus(pwd)}@{rest}"

    if "sslmode=" not in db_url and "sqlite" not in db_url:
        db_url += ("&" if "?" in db_url else "?") + "sslmode=require"

    try:
        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False
            engine_kwargs = {}
        else:
            connect_args["connect_timeout"] = 10
            if IS_VERCEL:
                # NullPool avoids stale/dead connections across serverless lambda freezes
                engine_kwargs = {
                    "poolclass": NullPool,
                    "pool_pre_ping": True,
                }
            else:
                engine_kwargs = {
                    "pool_size": 5,
                    "max_overflow": 5,
                    "pool_pre_ping": True,
                    "pool_recycle": 300,
                }
            
        temp_engine = create_engine(
            db_url,
            connect_args=connect_args,
            **engine_kwargs
        )
        # On local machine, test connection immediately so developers know if offline
        if not IS_VERCEL:
            with temp_engine.connect() as test_conn:
                print("Successfully connected to Supabase PostgreSQL database.")
        engine = temp_engine
    except Exception as e:
        print(f"Notice: DATABASE_URL initialization error ({e}).")
        if not IS_VERCEL:
            engine = None
        else:
            # On Vercel, always preserve the Supabase engine rather than falling back to empty /tmp SQLite
            engine = temp_engine if 'temp_engine' in locals() else None

# 2. If no DATABASE_URL, attempt local MySQL only when NOT on Vercel
if engine is None and not IS_VERCEL:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "irsh123")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_NAME = os.getenv("DB_NAME", "salsabeel_db")

    try:
        import pymysql
        init_conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS)
        with init_conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`;")
        init_conn.close()

        local_mysql_url = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
        engine = create_engine(local_mysql_url, pool_pre_ping=True, pool_recycle=300)
        with engine.connect() as conn:
            print("Successfully connected to local MySQL.")
    except Exception as e:
        print(f"Local MySQL not available: {e}. Falling back to SQLite.")
        engine = None

# 3. Fallback to SQLite (on Vercel use writable temp directory, locally use project directory)
if engine is None:
    import tempfile
    if IS_VERCEL:
        sqlite_path = os.path.join(tempfile.gettempdir(), "salsabeel.db")
    else:
        sqlite_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salsabeel.db")
    print(f"Using SQLite database at {sqlite_path}")
    engine = create_engine(
        f"sqlite:///{sqlite_path}",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
