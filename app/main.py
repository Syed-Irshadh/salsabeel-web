import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Depends, HTTPException, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app import models, database
from pydantic import BaseModel
from typing import List
import shutil
import uuid

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Salsabeel Academy")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Seed some initial courses if empty
def seed_courses(db: Session):
    if db.query(models.Course).count() == 0:
        courses = [
            models.Course(title="Introduction to Islamic History", description="A comprehensive overview of early Islamic history.", category="History", image_url="https://images.unsplash.com/photo-1584285404554-18451c23f2b6?auto=format&fit=crop&q=80&w=800", content="Chapter 1: The Pre-Islamic Era...", price="$49.00"),
            models.Course(title="Arabic Calligraphy Basics", description="Learn the beautiful art of Arabic writing.", category="Art", image_url="https://images.unsplash.com/photo-1543888372-5b9c647cb5c8?auto=format&fit=crop&q=80&w=800", content="Lesson 1: Tools and Materials...", price="$29.00"),
            models.Course(title="Quranic Recitation for Beginners", description="Master the rules of Tajweed.", category="Theology", image_url="https://images.unsplash.com/photo-1603507116515-5d9c223aeb29?auto=format&fit=crop&q=80&w=800", content="Module 1: Arabic Alphabet pronunciation...", price="$39.00")
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
    enrollments = db.query(models.Enrollment).options(joinedload(models.Enrollment.user), joinedload(models.Enrollment.course)).all()
    return templates.TemplateResponse(request=request, name="admin.html", context={"enrollments": enrollments})

@app.get("/viewer/{course_id}")
async def viewer_page(request: Request, course_id: int, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return templates.TemplateResponse(request=request, name="course_viewer.html", context={"course": course})

# API Routes
class CourseCreate(BaseModel):
    title: str
    description: str
    category: str
    image_url: str
    content: str
    price: str = "$49.00"

@app.post("/api/courses")
async def create_course(
    title: str = Form(...),
    description: str = Form(...),
    category: str = Form(...),
    content: str = Form(...),
    price: str = Form("$49.00"),
    image: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    upload_dir = os.path.join(BASE_DIR, "static", "img", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
        
    image_url = f"/static/img/uploads/{unique_filename}"
    
    db_course = models.Course(
        title=title,
        description=description,
        category=category,
        content=content,
        price=price,
        image_url=image_url
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@app.delete("/api/courses/{course_id}")
async def delete_course(course_id: int, db: Session = Depends(database.get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.query(models.Enrollment).filter(models.Enrollment.course_id == course_id).delete()
    db.delete(course)
    db.commit()
    return {"status": "success"}

class AuthRequest(BaseModel):
    email: str

@app.post("/api/auth")
async def mock_auth(data: AuthRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()
    if not user:
        role = "admin" if data.email == "admin@salsabeel.com" else "student"
        user = models.User(email=data.email, role=role, hashed_password="mock")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.id, "email": user.email, "role": user.role}

class EnrollmentCreate(BaseModel):
    user_id: int
    course_id: int

@app.post("/api/enrollments")
async def create_enrollment(data: EnrollmentCreate, db: Session = Depends(database.get_db)):
    existing = db.query(models.Enrollment).filter(
        models.Enrollment.user_id == data.user_id,
        models.Enrollment.course_id == data.course_id
    ).first()
    if not existing:
        enroll = models.Enrollment(user_id=data.user_id, course_id=data.course_id)
        db.add(enroll)
        db.commit()
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
