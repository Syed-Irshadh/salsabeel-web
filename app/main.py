import os
import sys
import json
import uuid
import shutil
import re
import warnings
import tempfile
import asyncio
import base64
import requests
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

import io
from typing import Optional
from PIL import Image
from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

# Ensure project root is in sys.path
BASE_DIR = str(Path(__file__).resolve().parent.parent)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from app import models, database, auth, email_service

load_dotenv()

def get_upload_dir() -> str:
    """Return upload directory path, ensuring resilience on Vercel serverless filesystem."""
    if os.getenv("VERCEL"):
        path = os.path.join(tempfile.gettempdir(), "uploads")
    else:
        path = os.path.join(BASE_DIR, "static", "img", "uploads")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(tempfile.gettempdir(), "uploads")
        os.makedirs(path, exist_ok=True)
    return path

def process_and_store_image(file_bytes: bytes, filename: str, db: Session) -> str:
    """
    Compresses image for rapid delivery, caches locally, and persists permanently in Supabase.
    Returns persistent URL path (/api/images/{unique_filename}).
    """
    file_ext = os.path.splitext(filename)[1].lower() if filename else ".jpg"
    if file_ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        file_ext = ".jpg"
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    content_type = "image/webp" if file_ext == ".webp" else ("image/png" if file_ext == ".png" else "image/jpeg")
    
    # Compress/resize image with Pillow
    try:
        img = Image.open(io.BytesIO(file_bytes))
        if img.mode in ("RGBA", "P") and file_ext in [".jpg", ".jpeg"]:
            img = img.convert("RGB")
            
        # Limit max dimension to 1400px to maintain pristine quality while saving storage
        img.thumbnail((1400, 1400), Image.Resampling.LANCZOS)
        
        out_buf = io.BytesIO()
        if file_ext in [".jpg", ".jpeg"]:
            img.save(out_buf, format="JPEG", quality=85, optimize=True)
            content_type = "image/jpeg"
        elif file_ext == ".png":
            img.save(out_buf, format="PNG", optimize=True)
            content_type = "image/png"
        elif file_ext == ".webp":
            img.save(out_buf, format="WEBP", quality=85)
            content_type = "image/webp"
        else:
            img.save(out_buf, format="JPEG", quality=85)
            content_type = "image/jpeg"
            
        final_bytes = out_buf.getvalue()
    except Exception as e:
        print(f"Notice: Pillow processing skipped ({e}), storing raw bytes.")
        final_bytes = file_bytes

    # Cache locally on disk for ultra-fast serving in this instance
    upload_dir = get_upload_dir()
    disk_path = os.path.join(upload_dir, unique_filename)
    try:
        with open(disk_path, "wb") as f:
            f.write(final_bytes)
    except Exception as e:
        print(f"Notice: local disk cache write skipped: {e}")

    # Persist in Supabase DB so serverless never loses the image
    try:
        db_file = models.UploadedFile(
            filename=unique_filename,
            content_type=content_type,
            data=final_bytes
        )
        db.add(db_file)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Warning: Could not save to uploaded_files table: {e}")

    return f"/api/images/{unique_filename}"

# Initialize database tables only in local development (never block serverless cold starts)
if not os.getenv("VERCEL"):
    try:
        models.Base.metadata.create_all(bind=database.engine)
    except Exception as e:
        print(f"Notice: Table creation deferred or handled: {e}")

app = FastAPI(title="Salsabeel Academy")

# Enable CORS for 3-Tier Architecture (Vercel Frontend <-> Render/Cloud Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Salsabeel Backend API",
        "architecture": "3-Tier (Vercel Frontend | Render Backend | Supabase DB)"
    }

@app.get("/api/db-check")
async def db_check():
    try:
        import psycopg2
        pg_status = f"psycopg2 imported successfully (version: {psycopg2.__version__})"
    except Exception as pe:
        pg_status = f"psycopg2 import failed: {pe}"

    from sqlalchemy import text
    try:
        with database.SessionLocal() as db:
            res = db.execute(text("SELECT count(*) FROM courses;")).fetchone()
            return {
                "status": "connected",
                "courses_count": res[0] if res else 0,
                "engine_url": str(database.engine.url) if database.engine else "None",
                "is_vercel": bool(os.getenv("VERCEL")),
                "psycopg2_status": pg_status,
                "db_init_error": database.DB_INIT_ERROR
            }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
            "engine_url": str(database.engine.url) if database.engine else "None",
            "is_vercel": bool(os.getenv("VERCEL")),
            "psycopg2_status": pg_status,
            "db_init_error": database.DB_INIT_ERROR
        }

@app.get("/api/images/{filename}")
@app.get("/static/img/uploads/{filename}")
async def serve_uploaded_image(filename: str, db: Session = Depends(database.get_db)):
    """
    Serves uploaded images reliably on Vercel and local environments.
    Checks fast local disk cache first, falls back to persistent Supabase PostgreSQL database.
    """
    upload_dir = get_upload_dir()
    disk_path = os.path.join(upload_dir, filename)
    
    # 1. Check local disk cache
    if os.path.exists(disk_path):
        ext = os.path.splitext(filename)[1].lower()
        media_type = "image/webp" if ext == ".webp" else ("image/png" if ext == ".png" else "image/jpeg")
        try:
            with open(disk_path, "rb") as f:
                content = f.read()
            return Response(content=content, media_type=media_type, headers={"Cache-Control": "public, max-age=86400, immutable"})
        except Exception:
            pass

    # 2. Query persistent Supabase DB
    db_file = db.query(models.UploadedFile).filter(models.UploadedFile.filename == filename).first()
    if db_file and db_file.data:
        # Cache to disk for instant next access in this container
        try:
            with open(disk_path, "wb") as f:
                f.write(db_file.data)
        except Exception:
            pass
        return Response(
            content=db_file.data,
            media_type=db_file.content_type or "image/jpeg",
            headers={"Cache-Control": "public, max-age=86400, immutable"}
        )
        
    raise HTTPException(status_code=404, detail="Image not found")

static_dir = os.path.join(BASE_DIR, "static")
if not os.path.exists(static_dir):
    try:
        os.makedirs(static_dir, exist_ok=True)
    except OSError:
        pass
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = os.path.join(BASE_DIR, "templates")
if not os.path.exists(templates_dir):
    for candidate in [os.path.join(os.getcwd(), "templates"), "/var/task/templates", os.path.join(os.path.dirname(BASE_DIR), "templates")]:
        if os.path.exists(candidate):
            templates_dir = candidate
            break
templates = Jinja2Templates(directory=templates_dir)

# Seed some initial courses if empty
def seed_courses(db: Session):
    if db.query(models.Course).count() == 0:
        courses = [
            models.Course(title="Introduction to Islamic History", description="A comprehensive overview of early Islamic history.", category="History", image_url="https://images.unsplash.com/photo-1584285404554-18451c23f2b6?auto=format&fit=crop&q=80&w=800", content="Chapter 1: The Pre-Islamic Era...", price="Free", start_date="Completed (July 2026)", status="past"),
            models.Course(title="Arabic Calligraphy Basics", description="Learn the beautiful art of Arabic writing.", category="Art", image_url="https://images.unsplash.com/photo-1543888372-5b9c647cb5c8?auto=format&fit=crop&q=80&w=800", content="Lesson 1: Tools and Materials...", price="Free", start_date="Ongoing (Mon & Wed)", status="current"),
            models.Course(title="Quranic Recitation for Beginners", description="Master the rules of Tajweed.", category="Theology", image_url="https://images.unsplash.com/photo-1603507116515-5d9c223aeb29?auto=format&fit=crop&q=80&w=800", content="Module 1: Arabic Alphabet pronunciation...", price="Free", start_date="Starts Next Month", status="upcoming")
        ]
        db.add_all(courses)
        db.commit()

# Safely call seed only in local dev environment
if not os.getenv("VERCEL"):
    try:
        with database.SessionLocal() as db:
            seed_courses(db)
    except Exception as e:
        print(f"Notice: Course seeding deferred or skipped: {e}")

@app.get("/")
async def home(request: Request, db: Session = Depends(database.get_db)):
    try:
        courses = db.query(models.Course).all()
    except Exception as e:
        print(f"Notice: Course query error on /: {e}")
        courses = []
    return templates.TemplateResponse(request=request, name="index.html", context={"courses": courses})

@app.get("/courses")
async def courses_page(request: Request, db: Session = Depends(database.get_db)):
    try:
        courses = db.query(models.Course).all()
    except Exception as e:
        print(f"Notice: Course query error on /courses: {e}")
        courses = []
    return templates.TemplateResponse(request=request, name="courses.html", context={"courses": courses})

@app.get("/about")
async def about_page(request: Request):
    return templates.TemplateResponse(request=request, name="about.html")

@app.get("/admin")
async def admin_page(request: Request, db: Session = Depends(database.get_db)):
    courses = db.query(models.Course).all()
    return templates.TemplateResponse(request=request, name="admin.html", context={"courses": courses})

@app.get("/api/admin/enrollments")
async def get_admin_enrollments(
    course_id: Optional[int] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    query = db.query(models.Enrollment).options(joinedload(models.Enrollment.user), joinedload(models.Enrollment.course))
    if course_id:
        query = query.filter(models.Enrollment.course_id == course_id)
    enrollments = query.order_by(models.Enrollment.enrolled_at.desc()).all()
    
    result = []
    for e in enrollments:
        student_name = e.user.name if (e.user and e.user.name) else (e.user.email.split("@")[0] if e.user and e.user.email else "Student")
        student_email = e.user.email if e.user else "Deleted User"
        course_title = e.course.title if e.course else "Unknown Course"
        course_category = e.course.category if e.course else "General"
        course_status = e.course.status if e.course else "current"
        
        result.append({
            "id": e.id,
            "student_id": e.user.id if e.user else None,
            "student_name": student_name,
            "student_email": student_email,
            "course_id": e.course.id if e.course else None,
            "course_title": course_title,
            "course_category": course_category,
            "course_status": course_status,
            "date": e.enrolled_at.strftime("%b %d, %Y %I:%M %p") if e.enrolled_at else "N/A"
        })
    return result

@app.delete("/api/admin/enrollments/{enrollment_id}")
async def delete_admin_enrollment(
    enrollment_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    enrollment = db.query(models.Enrollment).filter(models.Enrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment record not found")
        
    student_label = (enrollment.user.name or enrollment.user.email) if enrollment.user else "Student"
    course_title = enrollment.course.title if enrollment.course else "Course"
    
    db.delete(enrollment)
    db.commit()
    return {
        "status": "success",
        "message": f"Successfully removed {student_label} from {course_title}"
    }

def get_main_admin(db: Session) -> Optional[models.User]:
    """
    Identifies the Main/Primary Administrator.
    By default, the first administrator account created (lowest ID among admins),
    or admin@salsabeel.com.
    """
    admin_by_email = db.query(models.User).filter(
        models.User.email == "admin@salsabeel.com", 
        models.User.role == "admin"
    ).first()
    if admin_by_email:
        return admin_by_email
    return db.query(models.User).filter(models.User.role == "admin").order_by(models.User.id.asc()).first()

@app.get("/api/admin/admins")
async def get_admins(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    main_admin = get_main_admin(db)
    main_admin_id = main_admin.id if main_admin else None
    current_is_main = bool(main_admin_id and current_user.id == main_admin_id)
    
    admins = db.query(models.User).filter(models.User.role == "admin").order_by(models.User.id.asc()).all()
    admin_list = []
    for u in admins:
        is_main = bool(main_admin_id and u.id == main_admin_id)
        admin_list.append({
            "id": u.id,
            "name": u.name or (u.email.split("@")[0] if u.email else "Admin"),
            "email": u.email,
            "role": u.role,
            "is_main_admin": is_main
        })
        
    return {
        "current_user_is_main": current_is_main,
        "admins": admin_list
    }

class AdminCreateRequest(BaseModel):
    name: Optional[str] = ""
    email: str
    password: Optional[str] = None

@app.post("/api/admin/add-admin")
async def add_admin(
    data: AdminCreateRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    clean_email = data.email.strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    existing_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if existing_user:
        if existing_user.role == "admin":
            raise HTTPException(status_code=400, detail="This user is already an administrator")
        # Promote existing student to admin
        existing_user.role = "admin"
        if data.name and data.name.strip():
            existing_user.name = data.name.strip()
        if data.password and len(data.password.strip()) >= 8:
            existing_user.hashed_password = auth.get_password_hash(data.password.strip())
        db.commit()
        return {"status": "success", "message": f"Successfully promoted {clean_email} to Administrator!"}
    
    # New user: password required (min 8 chars)
    if not data.password or len(data.password.strip()) < 8:
        raise HTTPException(status_code=400, detail="A password of at least 8 characters is required for a new user.")
        
    new_admin = models.User(
        name=data.name.strip() if data.name else None,
        email=clean_email,
        hashed_password=auth.get_password_hash(data.password.strip()),
        role="admin"
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)
    return {"status": "success", "message": f"Successfully created new Administrator: {clean_email}"}

class AdminRemoveRequest(BaseModel):
    user_id: int

@app.post("/api/admin/remove-admin")
async def remove_admin(
    data: AdminRemoveRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    main_admin = get_main_admin(db)
    if not main_admin or current_user.id != main_admin.id:
        raise HTTPException(
            status_code=403, 
            detail="Permission Denied: Only the Main Administrator (the primary administrator account) can remove or demote other administrators."
        )
        
    if data.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot remove your own administrator privileges.")
        
    target_user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if target_user.id == main_admin.id:
        raise HTTPException(status_code=400, detail="The Main Administrator account cannot be demoted.")

    target_user.role = "student"
    db.commit()
    return {"status": "success", "message": f"Revoked administrator privileges for {target_user.email}"}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
        
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account.")
        
    target_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if target_user.role == "admin":
        main_admin = get_main_admin(db)
        if not main_admin or current_user.id != main_admin.id:
            raise HTTPException(
                status_code=403, 
                detail="Permission Denied: Only the Main Administrator can remove administrator accounts."
            )
            
    user_email = target_user.email
    db.query(models.Enrollment).filter(models.Enrollment.user_id == user_id).delete()
    db.delete(target_user)
    db.commit()
    return {"status": "success", "message": f"Successfully deleted user account: {user_email}"}

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

@app.post("/api/admin/change-password")
async def change_admin_password(
    data: ChangePasswordRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if not auth.verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long")
    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match")
        
    current_user.hashed_password = auth.get_password_hash(data.new_password)
    db.commit()
    return {"status": "success", "message": "Password changed successfully"}

@app.get("/viewer/{course_id}")
async def viewer_page(request: Request, course_id: int, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return templates.TemplateResponse(request=request, name="course_viewer.html", context={"course": course})

# API Routes
@app.post("/api/courses")
async def create_course(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    content: str = Form(...),
    price: str = Form("Free"),
    start_date: str = Form(""),
    status: str = Form("current"),
    image: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    final_image_url = None
    if image and image.filename:
        file_bytes = await image.read()
        final_image_url = process_and_store_image(file_bytes, image.filename, db)
    elif image_url and image_url.strip():
        final_image_url = image_url.strip()
    else:
        raise HTTPException(status_code=400, detail="Cover image is required.")
    
    effective_status = (status or "current").strip().lower()
    if effective_status not in ["current", "upcoming", "past"]:
        effective_status = determine_course_status(start_date or "", fallback_status="current")
        
    db_course = models.Course(
        title=title.strip(),
        description=description.strip(),
        category=category.strip(),
        content=content.strip(),
        price=price.strip() if price else "Free",
        start_date=start_date.strip() if start_date else None,
        status=effective_status,
        image_url=final_image_url
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.delete("/api/courses/{course_id}")
async def delete_course(
    course_id: int, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Clean up uploaded image file from Supabase and local cache
    if course.image_url:
        if course.image_url.startswith("/api/images/"):
            filename = os.path.basename(course.image_url)
            try:
                db.query(models.UploadedFile).filter(models.UploadedFile.filename == filename).delete()
            except Exception as err:
                print(f"Notice: could not delete persistent db file {filename}: {err}")
            filepath = os.path.join(get_upload_dir(), filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception:
                    pass
        elif course.image_url.startswith("/static/img/uploads/"):
            filename = os.path.basename(course.image_url)
            filepath = os.path.join(get_upload_dir(), filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except Exception as err:
                    print(f"Notice: could not delete local image file {filepath}: {err}")
    
    db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).delete()
    db.query(models.CourseRecording).filter(models.CourseRecording.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"status": "success"}

class UserCreate(BaseModel):
    name: str = ""
    email: str
    password: str

@app.post("/api/register")
async def register(user: UserCreate, db: Session = Depends(database.get_db)):
    if len(user.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
    clean_email = user.email.strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email is required")

    db_user = db.query(models.User).filter(models.User.email == clean_email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    role = "admin" if clean_email == "admin@salsabeel.com" else "student"
    new_user = models.User(
        name=user.name.strip() if user.name else None,
        email=clean_email,
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id, "name": new_user.name}

@app.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    clean_username = form_data.username.strip().lower()
    user = db.query(models.User).filter(models.User.email == clean_username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "user_id": user.id, "name": user.name or ""}

class ForgotPasswordRequest(BaseModel):
    email: str

class VerifyResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str
    confirm_password: str

@app.post("/api/auth/forgot-password/request")
async def request_password_reset(data: ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    clean_email = data.email.strip().lower()
    if not clean_email:
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    
    user = db.query(models.User).filter(models.User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No registered account found with this email address.")

    code = str(secrets.randbelow(900000) + 100000)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Invalidate previous unused codes for this email
    db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.email == clean_email,
        models.PasswordResetCode.used == 0
    ).update({"used": 2})

    reset_record = models.PasswordResetCode(
        email=clean_email,
        code=code,
        expires_at=expires_at,
        used=0
    )
    db.add(reset_record)
    db.commit()

    dispatch_res = email_service.send_password_reset_email(clean_email, code)
    
    if dispatch_res.get("delivered"):
        return {
            "status": "success",
            "message": "A 6-digit verification code has been sent to your email. Please check your Inbox and Spam / Junk folder.",
            "dev_code": None
        }
    elif dispatch_res.get("dev_mode"):
        return {
            "status": "success",
            "message": "SMTP credentials not configured in environment. Verification code provided below.",
            "dev_code": code
        }
    else:
        err_msg = dispatch_res.get("error", "SMTP delivery failed")
        return {
            "status": "warning",
            "message": f"Notice: Email dispatch issue ({err_msg}). Temporary code provided below for testing.",
            "dev_code": code,
            "error": err_msg
        }

@app.post("/api/auth/forgot-password/verify-and-reset")
async def verify_and_reset_password(data: VerifyResetPasswordRequest, db: Session = Depends(database.get_db)):
    clean_email = data.email.strip().lower()
    clean_code = data.code.strip()
    
    if not clean_email or not clean_code:
        raise HTTPException(status_code=400, detail="Email and reset code are required.")

    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters long.")

    if data.new_password != data.confirm_password:
        raise HTTPException(status_code=400, detail="New password and confirmation do not match.")

    user = db.query(models.User).filter(models.User.email == clean_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User account not found.")

    now_utc = datetime.now(timezone.utc)
    reset_entry = db.query(models.PasswordResetCode).filter(
        models.PasswordResetCode.email == clean_email,
        models.PasswordResetCode.code == clean_code,
        models.PasswordResetCode.used == 0
    ).order_by(models.PasswordResetCode.id.desc()).first()

    if not reset_entry:
        raise HTTPException(status_code=400, detail="Invalid reset code. Please check the code or request a new one.")

    exp = reset_entry.expires_at
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    
    if exp < now_utc:
        raise HTTPException(status_code=400, detail="This reset code has expired (valid for 15 mins). Please request a new code.")

    user.hashed_password = auth.get_password_hash(data.new_password)
    reset_entry.used = 1
    db.commit()

    return {
        "status": "success",
        "message": "Your password has been successfully reset! You can now sign in with your new password."
    }

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int

@app.post("/api/enrollments")
async def create_enrollment(
    data: EnrollmentCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    course = db.query(models.Course).filter(models.Course.id == data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
        
    user = db.query(models.User).filter(models.User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == data.user_id,
        models.Enrollment.course_id == data.course_id
    ).first()
    if not existing:
        enroll = models.Enrollment(user_id=data.user_id, course_id=data.course_id)
        db.add(enroll)
        db.commit()
    return {"status": "success"}

def determine_course_status(text: str, fallback_status: str = "current") -> str:
    """
    Intelligently determines whether a course is 'upcoming', 'current', or 'past'
    by comparing dates mentioned in start_date against today's date.
    """
    if not text:
        return fallback_status if fallback_status in ["current", "upcoming", "past"] else "current"
        
    text_lower = text.lower()
    if any(w in text_lower for w in ["completed", "finished", "ended"]):
        return "past"
    if any(w in text_lower for w in ["ongoing", "daily", "every week", "in progress"]):
        return "current"
        
    today = datetime.now().date()
    cleaned = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text, flags=re.IGNORECASE)
    
    # 1. Day Month Year: e.g. "07 October 2026", "7 Oct 2026"
    m1 = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', cleaned)
    if m1:
        for fmt in ['%d %B %Y', '%d %b %Y']:
            try:
                dt = datetime.strptime(f'{m1.group(1)} {m1.group(2)} {m1.group(3)}', fmt).date()
                if dt > today:
                    return 'upcoming'
                elif dt == today:
                    return 'current'
                else:
                    return 'past' if (today - dt).days > 30 else 'current'
            except ValueError:
                pass

    # 2. Month Day Year: e.g. "October 7, 2026", "Oct 7 2026"
    m2 = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', cleaned)
    if m2:
        for fmt in ['%B %d %Y', '%b %d %Y']:
            try:
                dt = datetime.strptime(f'{m2.group(1)} {m2.group(2)} {m2.group(3)}', fmt).date()
                if dt > today:
                    return 'upcoming'
                elif dt == today:
                    return 'current'
                else:
                    return 'past' if (today - dt).days > 30 else 'current'
            except ValueError:
                pass

    # 3. DD/MM/YYYY or DD-MM-YYYY: e.g. "05/09/2026"
    m3 = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', cleaned)
    if m3:
        try:
            dt = datetime.strptime(f'{m3.group(1)}/{m3.group(2)}/{m3.group(3)}', '%d/%m/%Y').date()
            if dt > today:
                return 'upcoming'
            elif dt == today:
                return 'current'
            else:
                return 'past' if (today - dt).days > 30 else 'current'
        except ValueError:
            pass

    return fallback_status if fallback_status in ["current", "upcoming", "past"] else "current"

@app.post("/api/parse-poster")
async def parse_poster(
    image: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    img_bytes = await image.read()
    saved_image_url = process_and_store_image(img_bytes, image.filename or "poster.jpg", db)
    
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return {
            "title": "",
            "description": "",
            "category": "General",
            "start_date": "",
            "status": "current",
            "price": "Free",
            "content": "",
            "image_url": saved_image_url,
            "error_notice": "Uploaded poster saved and attached below! GEMINI_API_KEY is not configured. Please fill in the course details manually below."
        }
    
    try:
        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        today_dt = datetime.now()
        today_str = today_dt.strftime("%d %B %Y")
        
        prompt = f"""
        Extract course information from this promotional poster image.
        Today's reference date is: {today_str}.

        Return ONLY a valid JSON object with these keys:
        - "title": string (Full course title)
        - "description": string (Short overview or subtitle)
        - "category": string (One of Theology, History, Art, Language, General)
        - "start_date": string (Start date/time or schedule if visible, e.g. "07 October 2026")
        - "status": string (CRITICAL: Compare course date against today's date ({today_str}):
            - "upcoming": If the course starts on a future date after today (e.g. October 2026 is after September 2026, so it is "upcoming")
            - "current": If the course starts today ({today_str}), is happening now, or is ongoing/recurring
            - "past": If the course has already completed in the past)
        - "price": string (Price if visible, otherwise "Free")
        - "content": string (Text outline of syllabus, instructor, contact info, etc.)
        """
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": image.content_type or "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        candidate_models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-flash-latest"]
        res_data = None
        last_error_text = None
        
        for m_name in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={api_key}"
            try:
                resp = await asyncio.to_thread(
                    requests.post,
                    url,
                    json=payload,
                    headers=headers,
                    timeout=45
                )
                if resp.status_code == 200:
                    json_body = resp.json()
                    candidates = json_body.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        if raw_text:
                            clean_text = raw_text.strip()
                            if clean_text.startswith("```json"):
                                clean_text = clean_text[7:]
                            if clean_text.startswith("```"):
                                clean_text = clean_text[3:]
                            if clean_text.endswith("```"):
                                clean_text = clean_text[:-3]
                            res_data = json.loads(clean_text.strip())
                            break
                else:
                    last_error_text = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as loop_err:
                last_error_text = str(loop_err)
                
        if not res_data:
            raise Exception(last_error_text or "Unable to extract details from poster.")
            
        data = res_data
        
        # Normalize fields for frontend
        title = data.get("title") or data.get("course_title") or ""
        desc = data.get("description") or ""
        cat = data.get("category") or "General"
        start = data.get("start_date") or ""
        price = data.get("price") or "Free"
        
        raw_status = str(data.get("status") or "current").lower().strip()
        status_val = determine_course_status(start, fallback_status=raw_status)
            
        content_val = data.get("content")
        if isinstance(content_val, dict):
            content_str = "\n".join([f"{k.replace('_', ' ').title()}: {v}" for k, v in content_val.items()])
        elif isinstance(content_val, list):
            content_str = "\n".join([str(item) for item in content_val])
        else:
            content_str = str(content_val or "")
            
        return {
            "title": title,
            "description": desc,
            "category": cat,
            "start_date": start,
            "status": status_val,
            "price": price,
            "content": content_str,
            "image_url": saved_image_url
        }
        
    except Exception as e:
        err_msg = str(e)
        notice = f"Uploaded poster saved and attached below! Note: AI text extraction issue ({err_msg}). Please fill in the course details manually below."
            
        return {
            "title": "",
            "description": "",
            "category": "General",
            "start_date": "",
            "status": "current",
            "price": "Free",
            "content": "",
            "image_url": saved_image_url,
            "error_notice": notice
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
