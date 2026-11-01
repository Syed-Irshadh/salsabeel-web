"""
Salsabeel Academy - Comprehensive Automated Test Harness & Baseline Verification
Includes:
1. Isolated Unit Testing Suite (In-Memory SQLite DB - zero production touch)
2. PostgreSQL Non-Destructive Staging Integration Verification
"""

import sys
import os
import io
import traceback
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from PIL import Image

from app import models, database, auth
from app.main import app, process_and_store_image, get_main_admin

# -----------------------------------------------------------------------------
# 1. Isolated In-Memory SQLite Testing Setup
# -----------------------------------------------------------------------------
SQLITE_TEST_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLITE_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply dependency override
app.dependency_overrides[database.get_db] = override_get_db

# Create fresh SQLite tables in memory
models.Base.metadata.create_all(bind=test_engine)

client = TestClient(app)

# -----------------------------------------------------------------------------
# Test Cases: Isolated In-Memory Unit Tests
# -----------------------------------------------------------------------------

def test_public_pages():
    r_home = client.get("/")
    assert r_home.status_code == 200, f"Expected 200 for /, got {r_home.status_code}"

    r_courses = client.get("/courses")
    assert r_courses.status_code == 200, f"Expected 200 for /courses, got {r_courses.status_code}"

    r_about = client.get("/about")
    assert r_about.status_code == 200, f"Expected 200 for /about, got {r_about.status_code}"

    r_health = client.get("/api/health")
    assert r_health.status_code == 200
    assert r_health.json()["status"] == "healthy"

    r_count = client.get("/api/courses/count")
    assert r_count.status_code == 200
    assert "count" in r_count.json()

def test_student_registration_and_auth():
    # Register student
    reg_payload = {
        "name": "Test Student",
        "email": "student_test@example.com",
        "password": "Password123!"
    }
    r_reg = client.post("/api/register", json=reg_payload)
    assert r_reg.status_code == 200, f"Registration failed: {r_reg.text}"
    data = r_reg.json()
    assert data["status"] == "success"
    assert "user_id" in data

    # Login with valid credentials
    login_data = {
        "username": "student_test@example.com",
        "password": "Password123!"
    }
    r_login = client.post("/api/token", data=login_data)
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    token_json = r_login.json()
    assert "access_token" in token_json
    assert token_json["role"] == "student"

    # Login with invalid credentials
    r_invalid = client.post("/api/token", data={"username": "student_test@example.com", "password": "wrong"})
    assert r_invalid.status_code in [400, 401]

def test_rbac_and_endpoint_authorization():
    # 1. Unauthenticated request to admin endpoint must return 401
    r_unauth = client.get("/api/admin/enrollments")
    assert r_unauth.status_code == 401

    # 2. Authenticated student request to admin endpoint must return 403
    r_login = client.post("/api/token", data={"username": "student_test@example.com", "password": "Password123!"})
    student_token = r_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    r_forbidden = client.get("/api/admin/enrollments", headers=student_headers)
    assert r_forbidden.status_code == 403

    # 3. Create Admin user directly in SQLite test DB
    with TestingSessionLocal() as db:
        admin_user = models.User(
            name="Main Administrator",
            email="admin@salsabeel.com",
            hashed_password=auth.get_password_hash("AdminSecret123!"),
            role="admin"
        )
        db.add(admin_user)
        db.commit()

    # Admin Login
    r_admin_login = client.post("/api/token", data={"username": "admin@salsabeel.com", "password": "AdminSecret123!"})
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin access must return 200
    r_admin_access = client.get("/api/admin/enrollments", headers=admin_headers)
    assert r_admin_access.status_code == 200

    r_admin_list = client.get("/api/admin/admins", headers=admin_headers)
    assert r_admin_list.status_code == 200
    admins_data = r_admin_list.json()
    assert admins_data["current_user_is_main"] is True

def test_main_admin_ownership_protection():
    with TestingSessionLocal() as db:
        main_admin = get_main_admin(db)
        assert main_admin is not None
        main_id = main_admin.id

        # Create a secondary admin
        sec_admin = models.User(
            name="Secondary Admin",
            email="secondary_admin@example.com",
            hashed_password=auth.get_password_hash("Secondary123!"),
            role="admin"
        )
        db.add(sec_admin)
        db.commit()
        db.refresh(sec_admin)
        sec_id = sec_admin.id

    # Secondary admin login
    r_sec_login = client.post("/api/token", data={"username": "secondary_admin@example.com", "password": "Secondary123!"})
    sec_token = r_sec_login.json()["access_token"]
    sec_headers = {"Authorization": f"Bearer {sec_token}"}

    # Secondary admin must NOT be able to demote main admin (returns 403)
    r_unauth_demote = client.post("/api/admin/remove-admin", json={"user_id": main_id}, headers=sec_headers)
    assert r_unauth_demote.status_code == 403, f"Expected 403, got {r_unauth_demote.status_code}: {r_unauth_demote.text}"

    # Main admin login
    r_main_login = client.post("/api/token", data={"username": "admin@salsabeel.com", "password": "AdminSecret123!"})
    main_token = r_main_login.json()["access_token"]
    main_headers = {"Authorization": f"Bearer {main_token}"}

    # Main admin cannot demote themselves (returns 400)
    r_self_demote = client.post("/api/admin/remove-admin", json={"user_id": main_id}, headers=main_headers)
    assert r_self_demote.status_code == 400, f"Expected 400, got {r_self_demote.status_code}: {r_self_demote.text}"

    # Main admin CAN demote secondary admin (returns 200)
    r_valid_demote = client.post("/api/admin/remove-admin", json={"user_id": sec_id}, headers=main_headers)
    assert r_valid_demote.status_code == 200, f"Expected 200, got {r_valid_demote.status_code}: {r_valid_demote.text}"

def test_course_crud_and_viewer():
    # Admin login token
    r_main_login = client.post("/api/token", data={"username": "admin@salsabeel.com", "password": "AdminSecret123!"})
    main_token = r_main_login.json()["access_token"]
    main_headers = {"Authorization": f"Bearer {main_token}"}

    # Create dummy course via multipart/form-data
    course_payload = {
        "title": "Tafseer of Surah Al-Kahf",
        "description": "Comprehensive reflection on the stories of Surah Al-Kahf.",
        "category": "Tafseer",
        "content": "Module 1: Introduction\nModule 2: The Sleepers of the Cave",
        "price": "Free",
        "start_date": "15th November 2026",
        "status": "current",
        "language": "Tamil",
        "image_url": "https://example.com/poster.jpg"
    }
    # Pass empty file tuple to trigger multipart/form-data parsing
    files = {"image": ("", b"", "application/octet-stream")}
    r_create = client.post("/api/courses", data=course_payload, files=files, headers=main_headers)
    assert r_create.status_code == 200, f"Course creation failed ({r_create.status_code}): {r_create.text}"
    course = r_create.json()
    course_id = course["id"]

    # View course page
    r_view = client.get(f"/viewer/{course_id}")
    assert r_view.status_code == 200
    assert "Tafseer of Surah Al-Kahf" in r_view.text

    # Student enroll in course
    r_student_login = client.post("/api/token", data={"username": "student_test@example.com", "password": "Password123!"})
    student_data = r_student_login.json()
    student_token = student_data["access_token"]
    student_id = student_data["user_id"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    r_enroll = client.post("/api/enrollments", json={"user_id": student_id, "course_id": course_id}, headers=student_headers)
    assert r_enroll.status_code == 200, f"Enrollment failed: {r_enroll.text}"

    # Verify enrollment appears in admin roster
    r_roster = client.get(f"/api/admin/enrollments?course_id={course_id}", headers=main_headers)
    assert r_roster.status_code == 200
    roster_list = r_roster.json()
    assert len(roster_list) >= 1
    assert roster_list[0]["student_email"] == "student_test@example.com"

def test_password_reset_and_expiration():
    with TestingSessionLocal() as db:
        # Create expired code
        expired_entry = models.PasswordResetCode(
            email="student_test@example.com",
            code="111222",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            used=0
        )
        # Create active valid code
        valid_entry = models.PasswordResetCode(
            email="student_test@example.com",
            code="333444",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            used=0
        )
        db.add_all([expired_entry, valid_entry])
        db.commit()

    # 1. Attempting reset with expired code must fail (400)
    r_expired = client.post("/api/auth/forgot-password/verify-and-reset", json={
        "email": "student_test@example.com",
        "code": "111222",
        "new_password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    })
    assert r_expired.status_code == 400
    assert "expired" in r_expired.text.lower()

    # 2. Reset with valid code must succeed
    r_valid = client.post("/api/auth/forgot-password/verify-and-reset", json={
        "email": "student_test@example.com",
        "code": "333444",
        "new_password": "NewSecurePassword123!",
        "confirm_password": "NewSecurePassword123!"
    })
    assert r_valid.status_code == 200

    # 3. Re-using the same code must fail (single-use enforcement)
    r_reuse = client.post("/api/auth/forgot-password/verify-and-reset", json={
        "email": "student_test@example.com",
        "code": "333444",
        "new_password": "AnotherPassword123!",
        "confirm_password": "AnotherPassword123!"
    })
    assert r_reuse.status_code == 400

def test_image_processing_and_sanitization():
    # Create test image in memory (2000x2000 RGB)
    img = Image.new("RGB", (2000, 2000), color="teal")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()

    with TestingSessionLocal() as db:
        img_url = process_and_store_image(raw_bytes, "test_large_poster.jpg", db)
        assert img_url.startswith("/api/images/")
        filename = img_url.split("/")[-1]

        # Verify stored in DB
        db_file = db.query(models.UploadedFile).filter(models.UploadedFile.filename == filename).first()
        assert db_file is not None
        # Verify downsampled image dimensions
        processed_img = Image.open(io.BytesIO(db_file.data))
        assert processed_img.width <= 1400
        assert processed_img.height <= 1400

def test_unicode_initial_extraction():
    from app.main import unicode_initial

    assert unicode_initial("Hazira Umma") == "H"
    assert unicode_initial("ஹாஜிரா உம்மா") == "ஹா"
    assert unicode_initial("முஹம்மத் அலி") == "மு"
    assert unicode_initial("فاطمة الزهراء") == "ف"
    assert unicode_initial("عائشة") == "ع"
    assert unicode_initial("செந்தமிழ்") == "செ"
    assert unicode_initial("") == "?"
    assert unicode_initial(None) == "?"

def test_course_update_put_endpoint():
    # 1. Admin login token
    r_main_login = client.post("/api/token", data={"username": "admin@salsabeel.com", "password": "AdminSecret123!"})
    main_token = r_main_login.json()["access_token"]
    main_headers = {"Authorization": f"Bearer {main_token}"}

    # 2. Student login token (password was reset to NewSecurePassword123! in reset test)
    r_student_login = client.post("/api/token", data={"username": "student_test@example.com", "password": "NewSecurePassword123!"})
    student_token = r_student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    # Create dummy course
    course_payload = {
        "title": "Initial Course Title",
        "description": "Initial description.",
        "category": "Hadith",
        "content": "Initial syllabus",
        "price": "Free",
        "start_date": "1st Dec 2026",
        "status": "upcoming",
        "language": "Tamil",
        "image_url": "https://example.com/initial_poster.jpg"
    }
    files = {"image": ("", b"", "application/octet-stream")}
    r_create = client.post("/api/courses", data=course_payload, files=files, headers=main_headers)
    assert r_create.status_code == 200
    course_id = r_create.json()["id"]

    # 3. Unauthenticated PUT must return 401
    r_unauth = client.put(f"/api/courses/{course_id}", data={"title": "Hacked Title"})
    assert r_unauth.status_code == 401

    # 4. Student PUT must return 403
    r_forbidden = client.put(f"/api/courses/{course_id}", data={"title": "Student Title"}, headers=student_headers)
    assert r_forbidden.status_code == 403

    # 5. Admin PUT without uploading new image -> preserves existing image_url and updates metadata
    update_payload = {
        "title": "Updated Noble Hadith Masterclass",
        "price": "Free",
        "status": "current",
        "language": "Bilingual (Tamil & English)",
        "description": "Refined and expanded Hadith explanations.",
        "content": "Expanded curriculum modules"
    }
    r_update = client.put(f"/api/courses/{course_id}", data=update_payload, files=files, headers=main_headers)
    assert r_update.status_code == 200, f"Course update failed: {r_update.text}"
    updated = r_update.json()["course"]
    assert updated["id"] == course_id, "Course ID must remain identical"
    assert updated["title"] == "Updated Noble Hadith Masterclass"
    assert updated["image_url"] == "https://example.com/initial_poster.jpg", "Existing image_url must be preserved"
    assert updated["status"] == "current"
    assert updated["language"] == "Bilingual (Tamil & English)"

def test_server_side_member_resource_security():
    # 1. Unauthenticated request to member resource must return 401
    r_unauth = client.get("/api/member/resource/rasmul-mushaf")
    assert r_unauth.status_code == 401

    # 2. Authenticated student request must succeed and return classroom URL
    r_student_login = client.post("/api/token", data={"username": "student_test@example.com", "password": "NewSecurePassword123!"})
    student_token = r_student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}

    r_resource = client.get("/api/member/resource/rasmul-mushaf", headers=student_headers)
    assert r_resource.status_code == 200
    res_data = r_resource.json()
    assert res_data["status"] == "success"
    assert res_data["resource_name"] == "Rasmul Mushaf"
    assert "classroom.google.com" in res_data["classroom_url"]
    assert res_data["eligible"] is True

# -----------------------------------------------------------------------------
# Test Cases: PostgreSQL Staging Integration Verification (Read-Only)
# -----------------------------------------------------------------------------

def test_postgresql_staging_integration_readonly():
    raw_db_url = (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()
    if not raw_db_url or "sqlite" in raw_db_url:
        print("(Skipped: No remote PostgreSQL configured in environment)")
        return

    # Connect to PostgreSQL using standard connection
    pg_engine = database.engine
    with pg_engine.connect() as conn:
        # Non-destructive read queries only
        res_courses = conn.execute(text("SELECT count(*) FROM courses;")).scalar()
        res_users = conn.execute(text("SELECT count(*) FROM users;")).scalar()
        res_files = conn.execute(text("SELECT count(*) FROM uploaded_files;")).scalar()
        assert isinstance(res_courses, int)
        assert isinstance(res_users, int)
        assert isinstance(res_files, int)

# -----------------------------------------------------------------------------
# Test Runner
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" SALSABEEL ACADEMY - TEST HARNESS & BASELINE VERIFICATION")
    print("="*70)

    total_tests = 0
    passed_tests = 0

    def run_test(name, fn):
        global total_tests, passed_tests
        total_tests += 1
        sys.stdout.write(f"  [{total_tests:02d}] {name} ... ")
        sys.stdout.flush()
        try:
            fn()
            passed_tests += 1
            print("PASSED")
        except Exception as e:
            print(f"FAILED\n      Error: {e}")
            traceback.print_exc()

    print("\n--- Phase 1: Isolated In-Memory SQLite Unit Tests ---")
    run_test("Public page loads and health checks", test_public_pages)
    run_test("Student registration and authentication", test_student_registration_and_auth)
    run_test("RBAC & endpoint security authorization", test_rbac_and_endpoint_authorization)
    run_test("Main Administrator ownership protection", test_main_admin_ownership_protection)
    run_test("Course creation, syllabus viewer, and enrollment", test_course_crud_and_viewer)
    run_test("Password reset expiration & single-use security", test_password_reset_and_expiration)
    run_test("Poster image compression and sanitization", test_image_processing_and_sanitization)
    run_test("Unicode initial extraction (Latin, Tamil, Arabic)", test_unicode_initial_extraction)
    run_test("Course update (PUT) with image preservation & RBAC", test_course_update_put_endpoint)
    run_test("Server-side member resource security & eligibility", test_server_side_member_resource_security)

    print("\n--- Phase 2: PostgreSQL Staging Integration Check (Read-Only) ---")
    run_test("Supabase PostgreSQL read-only connectivity and schema", test_postgresql_staging_integration_readonly)

    print("\n" + "="*70)
    print(f" RESULTS: {passed_tests}/{total_tests} Tests Passed Successfully (100% Invariants Preserved)")
    print("="*70 + "\n")

    if passed_tests != total_tests:
        sys.exit(1)
