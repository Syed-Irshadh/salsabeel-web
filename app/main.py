import os
import sys
import json
import uuid
import shutil
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from app import models, database, auth

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Salsabeel Academy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

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

# Call seed on startup
with database.SessionLocal() as db:
    seed_courses(db)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/courses")
async def courses_page(request: Request, db: Session = Depends(database.get_db)):
    courses = db.query(models.Course).all()
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
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    enrollments = db.query(models.Enrollment).options(joinedload(models.Enrollment.user), joinedload(models.Enrollment.course)).all()
    
    result = []
    for e in enrollments:
        result.append({
            "student_email": e.user.email,
            "course_title": e.course.title,
            "date": e.enrolled_at.strftime("%Y-%m-%d %H:%M")
        })
    return result

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
        upload_dir = os.path.join(BASE_DIR, "static", "img", "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
            
        final_image_url = f"/static/img/uploads/{unique_filename}"
    elif image_url and image_url.strip():
        final_image_url = image_url.strip()
    else:
        raise HTTPException(status_code=400, detail="Cover image is required.")
    
    db_course = models.Course(
        title=title,
        description=description,
        category=category,
        content=content,
        price=price,
        start_date=start_date,
        status=status,
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
    
    db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).delete()
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
        
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    role = "admin" if user.email == "admin@salsabeel.com" else "student"
    new_user = models.User(
        name=user.name.strip() if user.name else None,
        email=user.email.strip(),
        hashed_password=hashed_password,
        role=role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"status": "success", "user_id": new_user.id, "name": new_user.name}

@app.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer", "role": user.role, "user_id": user.id, "name": user.name or ""}

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int

@app.post("/api/enrollments")
async def create_enrollment(
    data: EnrollmentCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
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
    current_user: models.User = Depends(auth.get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Save uploaded poster file to uploads folder
    upload_dir = os.path.join(BASE_DIR, "static", "img", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    file_ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
    if not file_ext or file_ext.lower() not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
        file_ext = ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    img_bytes = await image.read()
    with open(file_path, "wb") as buffer:
        buffer.write(img_bytes)
        
    saved_image_url = f"/static/img/uploads/{unique_filename}"
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "title": "AI Parsed Course (Mock)",
            "description": "This is a mock description because GEMINI_API_KEY is not set.",
            "category": "General",
            "start_date": "Starts next Monday",
            "price": "$49.00",
            "content": "Lesson 1: Intro",
            "image_url": saved_image_url
        }
    
    try:
        genai.configure(api_key=api_key)
        
        today_dt = datetime.now()
        today_str = today_dt.strftime("%d %B %Y")
        
        prompt = f"""
        Extract course information from this promotional poster image.
        Today's reference date is: {today_str}.

        Return ONLY a JSON object with these keys:
        - "title": string (Full course title)
        - "description": string (Short overview or subtitle)
        - "category": string (One of Theology, History, Art, Language, General)
        - "start_date": string (Start date/time or schedule if visible, e.g. "07 October 2026")
        - "status": string (CRITICAL: Compare course date against today's date ({today_str}):
            - "upcoming": If the course starts on a future date after today (e.g. October 2026 is after September 2026, so it is "upcoming")
            - "current": If the course starts today ({today_str}), is happening now, or is ongoing/recurring
            - "past": If the course has already completed in the past)
        - "price": string (Price if visible, otherwise "$49.00")
        - "content": string (Text outline of syllabus, instructor, contact info, etc.)
        """
        
        # Use ultra-fast flash-lite model with async non-blocking execution
        model_name = "gemini-3.5-flash-lite"
        try:
            model = genai.GenerativeModel(model_name, generation_config={"response_mime_type": "application/json"})
            response = await model.generate_content_async([
                prompt,
                {"mime_type": image.content_type or "image/jpeg", "data": img_bytes}
            ])
        except Exception:
            model = genai.GenerativeModel("gemini-flash-lite-latest", generation_config={"response_mime_type": "application/json"})
            response = await model.generate_content_async([
                prompt,
                {"mime_type": image.content_type or "image/jpeg", "data": img_bytes}
            ])
            
        data = json.loads(response.text.strip())
        
        # Normalize fields for frontend
        title = data.get("title") or data.get("course_title") or ""
        desc = data.get("description") or ""
        cat = data.get("category") or "General"
        start = data.get("start_date") or ""
        price = data.get("price") or "$49.00"
        
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
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
