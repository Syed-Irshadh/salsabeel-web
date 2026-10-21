from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, LargeBinary
from sqlalchemy.orm import relationship
from app.database import Base

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True)
    content_type = Column(String(100), default="image/jpeg")
    data = Column(LargeBinary)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(Text)
    category = Column(String(100))
    image_url = Column(String(500))
    content = Column(Text)
    start_date = Column(String(100), nullable=True)
    status = Column(String(50), default="current")  # current, upcoming, past
    price = Column(String(50), default="Free", nullable=True)
    enrollments = relationship("Enrollment", back_populates="course")
    recordings = relationship("CourseRecording", back_populates="course", cascade="all, delete-orphan")

class CourseRecording(Base):
    __tablename__ = "course_recordings"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(200), index=True)
    youtube_url = Column(String(500), nullable=False)
    
    course = relationship("Course", back_populates="recordings")

class Enrollment(Base):
    __tablename__ = "enrollments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    enrolled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    role = Column(String(50), default="student")

    enrollments = relationship("Enrollment", back_populates="user")

class PasswordResetCode(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), index=True, nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0)  # 0 = active/unused, 1 = completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
