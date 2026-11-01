"""
Salsabeel Academy - Additive Database Migration Runner
Feature: Dynamic Course Status & YouTube Playlist URL Field

1. Dialect-aware additive DDL:
   - PostgreSQL: ALTER TABLE courses ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500);
   - SQLite: ALTER TABLE courses ADD COLUMN youtube_url VARCHAR(500);
2. Normalizes legacy status values: 'current' -> 'ongoing', 'past' -> 'completed'.
3. Single transaction guarantee with Core pre-flight audit and reflected snapshots before commit.
4. Genuine SQLite transactional DDL with proved rollback test.
5. Strict staging and production safety verification.
"""
import sys
import os
import argparse
from pathlib import Path
from collections import Counter
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import (
    create_engine, event, text, inspect, MetaData, Table, Column, String, Integer, Text as SqlText, insert
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool, NullPool
from app import models

def mask_db_url(url: str) -> str:
    """Masks database passwords in logs for security."""
    try:
        parsed = urlparse(url)
        if parsed.password:
            return url.replace(f":{parsed.password}@", ":***@")
        return url
    except Exception:
        return "DATABASE_URL_REDACTED"

def extract_db_identity(url: str) -> tuple:
    """Extracts (host, port, dbname) to uniquely identify a database instance."""
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    port = parsed.port or (5432 if "postgres" in parsed.scheme else None)
    dbname = parsed.path.strip("/")
    return (hostname, port, dbname)

def apply_migration_to_engine(target_engine, session_factory):
    """
    Applies transactional DDL and status migration within a single atomic transaction.
    Runs Core-based pre-flight audit and exhaustive integrity checks BEFORE committing.
    """
    dialect_name = target_engine.dialect.name

    # Step 1: Pre-flight status audit (Core SELECT status — DOES NOT QUERY youtube_url!)
    with target_engine.connect() as audit_conn:
        inspector = inspect(audit_conn)
        if "courses" not in inspector.get_table_names():
            raise RuntimeError("Table 'courses' does not exist in target database.")

        status_rows = audit_conn.execute(text("SELECT status FROM courses;")).fetchall()
        statuses = [r[0] for r in status_rows]
        
        display_counts = Counter(s if s is not None else "<NULL>" for s in statuses)
        print("\n--- Pre-Flight Status Audit (Core SQL) ---")
        for s, count in sorted(display_counts.items()):
            print(f"  Status '{s}': {count} course(s)")

        allowed_pre_migration = {"upcoming", "current", "past", "ongoing", "completed"}
        unexpected = [s for s in statuses if s is None or not str(s).strip() or str(s).strip() not in allowed_pre_migration]
        if unexpected:
            raise RuntimeError(
                f"PRE-FLIGHT ABORT: Invalid or unexpected course status values detected: {unexpected}. "
                f"Migration stopped before modifying any records."
            )

        num_to_normalize = display_counts.get("current", 0) + display_counts.get("past", 0)
        print(f"  Courses to normalize ('current' -> 'ongoing', 'past' -> 'completed'): {num_to_normalize}")
        print("--- [OK] Pre-Flight Status Audit Passed ---")

    # Step 2: Open single connection and atomic transaction
    with target_engine.connect() as conn:
        if dialect_name == "sqlite":
            conn.exec_driver_sql("BEGIN TRANSACTION;")
        else:
            trans = conn.begin()

        db = session_factory(bind=conn)
        try:
            # Step 3: Snapshot BEFORE using Reflected Table (autoloaded before adding column)
            ref_meta = MetaData()
            courses_reflected = Table("courses", ref_meta, autoload_with=conn)
            existing_col_names = [c.name for c in courses_reflected.c]

            before_rows = conn.execute(courses_reflected.select()).fetchall()
            courses_before = {
                row._mapping[courses_reflected.c.id]: {
                    col.name: row._mapping[col] for col in courses_reflected.c
                }
                for row in before_rows
            }

            enrollments_before = {
                e.id: (e.user_id, e.course_id) for e in db.query(models.Enrollment).all()
            }
            recordings_before = {
                r.id: (r.course_id, r.title, r.youtube_url) for r in db.query(models.CourseRecording).all()
            }

            print(f"  [i] Pre-migration snapshot: {len(courses_before)} courses, {len(enrollments_before)} enrollments, {len(recordings_before)} recordings.")

            # Step 4: Transactional DDL
            if 'youtube_url' not in existing_col_names:
                if dialect_name == "postgresql":
                    conn.execute(text("ALTER TABLE courses ADD COLUMN IF NOT EXISTS youtube_url VARCHAR(500);"))
                else:
                    conn.execute(text("ALTER TABLE courses ADD COLUMN youtube_url VARCHAR(500);"))
                print(f"  [OK] ({dialect_name}) Transactional DDL: Added 'youtube_url' column.")
            else:
                print(f"  [OK] ({dialect_name}) Column 'youtube_url' already exists.")

            # Step 5: Data Normalization (flushed, identity map expired)
            updated_current = db.query(models.Course).filter(models.Course.status == 'current').update(
                {"status": "ongoing"}, synchronize_session="fetch"
            )
            updated_past = db.query(models.Course).filter(models.Course.status == 'past').update(
                {"status": "completed"}, synchronize_session="fetch"
            )
            db.flush()
            db.expire_all()

            print(f"  [OK] Normalized {updated_current} courses ('current' -> 'ongoing').")
            print(f"  [OK] Normalized {updated_past} courses ('past' -> 'completed').")

            # Step 6: Snapshot AFTER using the SAME Reflected Table (BEFORE COMMIT!)
            after_rows = conn.execute(courses_reflected.select()).fetchall()
            courses_after = {
                row._mapping[courses_reflected.c.id]: {
                    col.name: row._mapping[col] for col in courses_reflected.c
                }
                for row in after_rows
            }

            enrollments_after = {
                e.id: (e.user_id, e.course_id) for e in db.query(models.Enrollment).all()
            }
            recordings_after = {
                r.id: (r.course_id, r.title, r.youtube_url) for r in db.query(models.CourseRecording).all()
            }

            assert set(courses_before.keys()) == set(courses_after.keys()), "Integrity Error: Course IDs set mismatch!"
            assert len(courses_before) == len(courses_after), "Integrity Error: Course count changed!"
            assert enrollments_before == enrollments_after, "Integrity Error: Enrollment relationships altered!"
            assert recordings_before == recordings_after, "Integrity Error: Course recordings altered!"

            for cid, before in courses_before.items():
                after = courses_after[cid]
                for col_name, before_val in before.items():
                    if col_name == "status":
                        if before_val == "current":
                            assert after["status"] == "ongoing", f"Course {cid} 'current' was not migrated to 'ongoing'!"
                        elif before_val == "past":
                            assert after["status"] == "completed", f"Course {cid} 'past' was not migrated to 'completed'!"
                        else:
                            assert after["status"] == before_val, f"Course {cid} status unexpectedly modified!"
                    else:
                        assert after[col_name] == before_val, (
                            f"Integrity Error: Column '{col_name}' altered on course {cid}! "
                            f"Before: {repr(before_val)} vs After: {repr(after[col_name])}"
                        )

            # Step 7: Verify newly added column is accessible in database
            inspector_after = inspect(conn)
            cols_now = [c['name'] for c in inspector_after.get_columns('courses')]
            assert "youtube_url" in cols_now, "Integrity Error: youtube_url column missing post-DDL!"

            # Step 8: Final Transaction Commit (ONLY after all assertions pass)
            if dialect_name == "sqlite":
                conn.exec_driver_sql("COMMIT;")
            else:
                trans.commit()

            print("  [OK] Integrity verified: 100% of all existing columns, IDs, relations, and posters intact.")
            print("  [OK] Transaction committed successfully.")

        except Exception as e:
            if dialect_name == "sqlite":
                conn.exec_driver_sql("ROLLBACK;")
            else:
                trans.rollback()
            print(f"\n[FAIL] MIGRATION ABORTED: Transaction rolled back cleanly: {e}", file=sys.stderr)
            raise
        finally:
            db.close()

def test_migration_on_isolated_sqlite():
    """Runs deliberate rollback test followed by full migration and integrity tests on SQLite."""
    print("\n--- Test Suite A: Deliberate SQLite Rollback Test ---")
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    @event.listens_for(test_engine, 'connect')
    def set_sqlite_autocommit(dbapi_con, con_record):
        dbapi_con.isolation_level = None

    TestingSession = sessionmaker(autocommit=False, autoflush=False)

    pre_meta = MetaData()
    # Reconstruct pre-migration schema omitting youtube_url
    courses_old_table = Table(
        'courses', pre_meta,
        Column('id', Integer, primary_key=True, index=True),
        Column('title', String(255), index=True),
        Column('description', SqlText),
        Column('category', String(100)),
        Column('image_url', String(500)),
        Column('content', SqlText),
        Column('start_date', String(100), nullable=True),
        Column('status', String(50), default="current"),
        Column('price', String(50), default="Free", nullable=True),
        Column('language', String(100), default="Tamil", nullable=True)
    )

    for t in models.Base.metadata.sorted_tables:
        if t.name != 'courses':
            t.to_metadata(pre_meta)

    pre_meta.create_all(test_engine)

    # Populate initial records using Core insert
    with test_engine.connect() as conn:
        conn.execute(insert(courses_old_table).values([
            {
                "id": 1, "title": "Course One", "description": "Desc 1", "content": "Content 1",
                "category": "Hadith", "image_url": "/static/img/poster1.jpg", "price": "Free",
                "language": "Tamil", "start_date": "01 Oct 2026", "status": "current"
            },
            {
                "id": 2, "title": "Course Two", "description": "Desc 2", "content": "Content 2",
                "category": "Fiqh", "image_url": "/static/img/poster2.jpg", "price": "Free",
                "language": "Tamil", "start_date": "01 Jan 2026", "status": "past"
            },
            {
                "id": 3, "title": "Course Three", "description": "Desc 3", "content": "Content 3",
                "category": "Tafseer", "image_url": "/static/img/poster3.jpg", "price": "Free",
                "language": "Tamil", "start_date": "15 Dec 2026", "status": "upcoming"
            }
        ]))
        conn.commit()

    # Deliberate failure test
    with test_engine.connect() as conn:
        conn.exec_driver_sql("BEGIN TRANSACTION;")
        db = TestingSession(bind=conn)
        try:
            conn.execute(text("ALTER TABLE courses ADD COLUMN youtube_url VARCHAR(500);"))
            db.query(models.Course).filter(models.Course.status == 'current').update(
                {"status": "ongoing"}, synchronize_session="fetch"
            )
            db.flush()
            # Verify uncommitted state has column
            cols_uncommitted = [c['name'] for c in inspect(conn).get_columns('courses')]
            assert "youtube_url" in cols_uncommitted
            # Raise deliberate failure
            raise RuntimeError("SIMULATED ERROR FOR ROLLBACK VERIFICATION")
        except RuntimeError as e:
            conn.exec_driver_sql("ROLLBACK;")
            print(f"  [OK] Caught deliberate failure: {e}")
        finally:
            db.close()

    # Post-rollback inspection: verify database state
    with test_engine.connect() as conn:
        cols_after = [c['name'] for c in inspect(conn).get_columns('courses')]
        assert "youtube_url" not in cols_after, "Rollback failed: youtube_url column persists!"
        
        status_c1 = conn.execute(text("SELECT status FROM courses WHERE id=1;")).scalar()
        assert status_c1 == "current", f"Rollback failed: Course 1 status '{status_c1}' != 'current'!"
        
        status_c2 = conn.execute(text("SELECT status FROM courses WHERE id=2;")).scalar()
        assert status_c2 == "past", f"Rollback failed: Course 2 status '{status_c2}' != 'past'!"

        total_courses = conn.execute(text("SELECT count(*) FROM courses;")).scalar()
        assert total_courses == 3, f"Rollback failed: course count changed ({total_courses})!"
        print("  [OK] Rollback verified: youtube_url column removed and statuses restored to 'current' and 'past'.")

    print("\n--- Test Suite B: Full SQLite Migration & Reflected Snapshot Test ---")
    apply_migration_to_engine(test_engine, TestingSession)
    print("--- [OK] Pre-Flight SQLite Test Suite Passed Successfully ---")

def main():
    parser = argparse.ArgumentParser(description="Salsabeel Academy - Additive Database Migration Runner")
    parser.add_argument("--target", required=True, choices=["sqlite-test", "staging", "production"],
                        help="Target migration environment. Explicit selection required.")
    parser.add_argument("--db-url", required=False, default=None,
                        help="Database connection URL for target environment.")
    parser.add_argument("--confirm-production", action="store_true", default=False,
                        help="Safety confirmation flag strictly required when target is 'production'.")
    args = parser.parse_args()

    print("=" * 60)
    print(" SALSABEEL ACADEMY - DATABASE MIGRATION RUNNER")
    print(" Feature: Dynamic Course Status & YouTube Playlist URL")
    print(f" Target Environment: {args.target}")
    print("=" * 60)

    if args.target == "sqlite-test":
        test_migration_on_isolated_sqlite()
        print("\n[OK] SQLite Pre-Flight Tests Completed Successfully.")
        return

    if args.target == "staging":
        staging_url = args.db_url or os.getenv("STAGING_DATABASE_URL")
        if not staging_url:
            print("\n[FAIL] ERROR: No staging database URL provided.", file=sys.stderr)
            print("Pass '--db-url <URL>' or set environment variable 'STAGING_DATABASE_URL'.", file=sys.stderr)
            print("Safety Rule: Never falling back to 'DATABASE_URL' for staging target.", file=sys.stderr)
            sys.exit(1)

        prod_url = os.getenv("DATABASE_URL") or os.getenv("PROD_DATABASE_URL")
        if prod_url:
            staging_id = extract_db_identity(staging_url)
            prod_id = extract_db_identity(prod_url)
            if staging_id == prod_id:
                print(f"\n[FAIL] SAFETY ABORT: Staging database matches production database identity: {staging_id[0]}/{staging_id[2]}.", file=sys.stderr)
                print("Refusing to execute staging migration on production database instance.", file=sys.stderr)
                sys.exit(1)

        print(f"Connecting to staging database: {mask_db_url(staging_url)}")
        engine = create_engine(staging_url, poolclass=NullPool)
        Session = sessionmaker(autocommit=False, autoflush=False)
        apply_migration_to_engine(engine, Session)
        print("\n============================================================")
        print(" STAGING MIGRATION COMPLETED SUCCESSFULLY")
        print("============================================================")
        return

    if args.target == "production":
        if not args.confirm_production:
            print("\n[FAIL] SAFETY ABORT: Target is 'production' but '--confirm-production' flag is missing.", file=sys.stderr)
            print("To run in production, explicitly provide '--target production --confirm-production'.", file=sys.stderr)
            print("Prerequisite: A confirmed full database backup must be taken prior to production execution.", file=sys.stderr)
            sys.exit(1)

        prod_url = args.db_url or os.getenv("DATABASE_URL") or os.getenv("PROD_DATABASE_URL")
        if not prod_url:
            print("\n[FAIL] ERROR: No production database URL provided.", file=sys.stderr)
            sys.exit(1)

        print(f"Connecting to production database: {mask_db_url(prod_url)}")
        engine = create_engine(prod_url, poolclass=NullPool)
        Session = sessionmaker(autocommit=False, autoflush=False)
        apply_migration_to_engine(engine, Session)
        print("\n============================================================")
        print(" PRODUCTION MIGRATION COMPLETED SUCCESSFULLY")
        print("============================================================")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[FAIL] MIGRATION FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
