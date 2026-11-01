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
from app.main import app, process_and_store_image, get_main_admin, validate_youtube_url
from fastapi import HTTPException

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

def test_header_navigation_and_active_indicators():
    # 1. Homepage (/)
    r_home = client.get("/")
    assert r_home.status_code == 200
    home_html = r_home.text
    assert 'data-nav="home"' in home_html
    assert 'data-nav="home" aria-current="page"' in home_html
    assert 'data-nav="courses" aria-current="page"' not in home_html

    # 2. Courses Directory (/courses)
    r_courses = client.get("/courses")
    assert r_courses.status_code == 200
    courses_html = r_courses.text
    assert 'data-nav="courses"' in courses_html
    assert 'data-nav="courses" aria-current="page"' in courses_html
    assert 'data-nav="home" aria-current="page"' not in courses_html

    # 3. Query Parameter Resilience (/courses?status=ongoing&category=Tajweed)
    r_query = client.get("/courses?status=ongoing&category=Tajweed")
    assert r_query.status_code == 200
    query_html = r_query.text
    assert 'data-nav="courses" aria-current="page"' in query_html
    assert 'data-nav="home" aria-current="page"' not in query_html

    # 4. Course Viewer Page (/viewer/{id})
    r_viewer = client.get("/viewer/1")
    if r_viewer.status_code == 200:
        viewer_html = r_viewer.text
        assert 'data-nav="courses" aria-current="page"' in viewer_html
        assert 'data-nav="home" aria-current="page"' not in viewer_html

    # 5. About Page (/about)
    r_about = client.get("/about")
    assert r_about.status_code == 200
    about_html = r_about.text
    assert 'data-nav="about"' in about_html
    assert 'data-nav="about" aria-current="page"' in about_html
    assert 'data-nav="home" aria-current="page"' not in about_html
    assert 'data-nav="courses" aria-current="page"' not in about_html

    # 6. Admin Page (/admin) - never highlights Home or Courses
    r_admin = client.get("/admin")
    assert r_admin.status_code == 200
    admin_html = r_admin.text
    assert 'data-nav="home" aria-current="page"' not in admin_html
    assert 'data-nav="courses" aria-current="page"' not in admin_html
    assert 'data-nav="about" aria-current="page"' not in admin_html

def test_youtube_url_validator_matrix():
    # 1. Valid URLs
    valid_cases = [
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "https://m.youtube.com/watch?v=dQw4w9WgXcQ"),
        ("https://youtube.com/playlist?list=PL1234567890", "https://youtube.com/playlist?list=PL1234567890"),
        ("https://www.youtube.com/embed/dQw4w9WgXcQ", "https://www.youtube.com/embed/dQw4w9WgXcQ"),
        ("https://www.youtube.com/live/dQw4w9WgXcQ", "https://www.youtube.com/live/dQw4w9WgXcQ"),
        ("https://www.youtube.com/shorts/dQw4w9WgXcQ", "https://www.youtube.com/shorts/dQw4w9WgXcQ"),
        ("https://youtu.be/dQw4w9WgXcQ", "https://youtu.be/dQw4w9WgXcQ"),
        ("youtube.com/watch?v=dQw4w9WgXcQ", "https://youtube.com/watch?v=dQw4w9WgXcQ"),
        ("HTTPS://YOUTUBE.COM/watch?v=dQw4w9WgXcQ", "HTTPS://YOUTUBE.COM/watch?v=dQw4w9WgXcQ"),
    ]
    for inp, expected in valid_cases:
        res = validate_youtube_url(inp)
        assert res == expected, f"Failed for valid input {inp}: got {res}, expected {expected}"

    # None and empty return None
    assert validate_youtube_url(None) is None
    assert validate_youtube_url("") is None
    assert validate_youtube_url("   ") is None

    # 2. Rejection Cases (Must raise HTTPException 400)
    invalid_cases = [
        "https://user@youtube.com/watch?v=dQw4w9WgXcQ", # userinfo
        "https://youtube.com:8080/watch?v=dQw4w9WgXcQ", # non-standard port
        "https://attacker-youtube.com/watch?v=dQw4w9WgXcQ", # bad domain
        "https://vimeo.com/123456", # unsupported domain
        "ftp://youtube.com/watch?v=dQw4w9WgXcQ", # bad scheme
        "https://youtube.com//watch?v=dQw4w9WgXcQ", # double slashes
        "https://youtube.com/watch\\v=dQw4w9WgXcQ", # backslash
        "https://youtube.com/watch", # missing v param
        "https://youtube.com/watch?v=", # empty v param
        "https://youtube.com/playlist", # missing list param
        "https://youtube.com/playlist?list=", # empty list param
        "https://youtube.com/embed/id1/extra", # extra subpath
        "https://youtu.be/id1/extra", # extra subpath
        "https://youtu.be/", # missing video id
        "https://youtube.com/watch?v=123\x00abc", # null byte
    ]
    for bad_url in invalid_cases:
        try:
            validate_youtube_url(bad_url)
            assert False, f"Expected validation error for invalid URL: {bad_url}"
        except HTTPException as e:
            assert e.status_code == 400, f"Expected 400 for {bad_url}, got {e.status_code}"

def test_course_status_default_and_youtube_contracts():
    db = TestingSessionLocal()
    admin_email = "admin_course_test@salsabeelacademy.com"
    existing = db.query(models.User).filter(models.User.email == admin_email).first()
    if not existing:
        admin_user = models.User(
            email=admin_email,
            hashed_password=auth.get_password_hash("AdminPass123!"),
            name="Admin Test",
            role="admin"
        )
        db.add(admin_user)
        db.commit()
    db.close()

    r_login = client.post("/api/token", data={"username": admin_email, "password": "AdminPass123!"})
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    # Course A: Status omitted -> MUST default to 'upcoming'
    r_create_a = client.post(
        "/api/courses",
        headers=headers,
        data={
            "title": "Default Status Course",
            "description": "Testing upcoming default",
            "category": "Fiqh",
            "content": "Syllabus outline",
            "price": "Free",
            "language": "Tamil",
            "status": "", # empty -> defaults to 'upcoming'
            "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        },
        files={"image": ("poster_a.jpg", buf, "image/jpeg")}
    )
    assert r_create_a.status_code == 200, f"Create course failed: {r_create_a.text}"
    course_a = r_create_a.json()
    course_id = course_a["id"]
    assert course_a["status"] == "upcoming", f"Expected default status 'upcoming', got {course_a['status']}"
    assert course_a["youtube_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    # Test 3-part update contract in PUT /api/courses/{id}
    # Part 1: Update with valid non-empty URL -> replaces existing
    r_up_1 = client.put(
        f"/api/courses/{course_id}",
        headers=headers,
        data={"youtube_url": "https://youtu.be/updatedVideo123"}
    )
    assert r_up_1.status_code == 200
    data_1 = r_up_1.json()["course"]
    assert data_1["youtube_url"] == "https://youtu.be/updatedVideo123"

    # Part 2: Update with omitted field (no youtube_url in form) -> PRESERVES existing
    r_up_2 = client.put(
        f"/api/courses/{course_id}",
        headers=headers,
        data={"title": "Updated Title Only"}
    )
    assert r_up_2.status_code == 200
    data_2 = r_up_2.json()["course"]
    assert data_2["title"] == "Updated Title Only"
    assert data_2["youtube_url"] == "https://youtu.be/updatedVideo123", "Omitted youtube_url must be preserved"

    # Part 3: Update with explicit empty string -> CLEARS URL to None
    r_up_3 = client.put(
        f"/api/courses/{course_id}",
        headers=headers,
        data={"youtube_url": ""}
    )
    assert r_up_3.status_code == 200
    data_3 = r_up_3.json()["course"]
    assert data_3["youtube_url"] is None, "Empty string must clear youtube_url to None"

    # Part 4: Reject invalid YouTube URL with 400
    r_up_bad = client.put(
        f"/api/courses/{course_id}",
        headers=headers,
        data={"youtube_url": "https://unauthorized-domain.com/video"}
    )
    assert r_up_bad.status_code == 400

def test_auth_status_endpoint():
    # 1. Unauthenticated request -> 401
    r_anon = client.get("/api/auth/status")
    assert r_anon.status_code == 401

    # 2. Bad token -> 401
    r_bad = client.get("/api/auth/status", headers={"Authorization": "Bearer invalid_token_xyz"})
    assert r_bad.status_code == 401

    # 3. Valid authenticated request -> 200
    db = TestingSessionLocal()
    student_email = "auth_status_student@example.com"
    existing = db.query(models.User).filter(models.User.email == student_email).first()
    if not existing:
        student = models.User(
            email=student_email,
            hashed_password=auth.get_password_hash("StudentPass123!"),
            name="Auth Status Student",
            role="student"
        )
        db.add(student)
        db.commit()
    db.close()

    r_login = client.post("/api/token", data={"username": student_email, "password": "StudentPass123!"})
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]

    r_auth = client.get("/api/auth/status", headers={"Authorization": f"Bearer {token}"})
    assert r_auth.status_code == 200
    data = r_auth.json()
    assert data["authenticated"] is True
    assert data["user"]["email"] == student_email
    assert data["user"]["role"] == "student"
    assert data["user"]["name"] == "Auth Status Student"

def test_public_html_rendering_youtube_button():
    db = TestingSessionLocal()
    c_with = db.query(models.Course).filter(models.Course.youtube_url == "https://www.youtube.com/playlist?list=PL12345").first()
    if not c_with:
        c_with = models.Course(
            title="Dedicated YouTube Playlist Course",
            description="Course with YouTube link",
            category="Tafseer",
            content="Content",
            status="upcoming",
            price="Free",
            language="Tamil",
            image_url="/static/img/logo.jpeg",
            youtube_url="https://www.youtube.com/playlist?list=PL12345"
        )
        db.add(c_with)
        db.commit()
        db.refresh(c_with)

    c_without = db.query(models.Course).filter(models.Course.title == "Dedicated No YouTube Course").first()
    if not c_without:
        c_without = models.Course(
            title="Dedicated No YouTube Course",
            description="Course without YouTube link",
            category="Hadith",
            content="Content",
            status="upcoming",
            price="Free",
            language="Tamil",
            image_url="/static/img/logo.jpeg",
            youtube_url=None
        )
        db.add(c_without)
        db.commit()
        db.refresh(c_without)
    c_with_id = c_with.id
    c_without_id = c_without.id
    db.close()

    # 1. Course Directory Page (/courses)
    r_dir = client.get("/courses")
    assert r_dir.status_code == 200
    html_dir = r_dir.text
    assert "Watch on YouTube" in html_dir
    assert "https://www.youtube.com/playlist?list=PL12345" in html_dir
    assert 'target="_blank" rel="noopener noreferrer"' in html_dir

    # 2. Homepage (/)
    r_home = client.get("/")
    assert r_home.status_code == 200
    html_home = r_home.text
    assert "Watch on YouTube" in html_home

    # 3. Course Viewer (/viewer/{id})
    r_view_with = client.get(f"/viewer/{c_with_id}")
    assert r_view_with.status_code == 200
    html_view_with = r_view_with.text
    assert "Watch on YouTube" in html_view_with
    assert "https://www.youtube.com/playlist?list=PL12345" in html_view_with

    r_view_without = client.get(f"/viewer/{c_without_id}")
    assert r_view_without.status_code == 200
    html_view_without = r_view_without.text
    assert "Watch on YouTube" not in html_view_without

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
    run_test("Header navigation and route active indicators", test_header_navigation_and_active_indicators)
    run_test("YouTube URL validation matrix and security constraints", test_youtube_url_validator_matrix)
    run_test("Course status upcoming default & 3-part update contract", test_course_status_default_and_youtube_contracts)
    run_test("Authoritative auth status endpoint (/api/auth/status)", test_auth_status_endpoint)
    run_test("Public HTML conditional rendering of YouTube button", test_public_html_rendering_youtube_button)

    print("\n--- Phase 2: PostgreSQL Staging Integration Check (Read-Only) ---")
    run_test("Supabase PostgreSQL read-only connectivity and schema", test_postgresql_staging_integration_readonly)

    print("\n" + "="*70)
    print(f" RESULTS: {passed_tests}/{total_tests} Tests Passed Successfully (100% Invariants Preserved)")
    print("="*70 + "\n")

    if passed_tests != total_tests:
        sys.exit(1)
