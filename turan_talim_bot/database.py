import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

from config import Config

# Create async engine
engine = create_async_engine(Config.DATABASE_URL, echo=True)
Base = declarative_base()

# Create async session
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Define models
class Teacher(Base):
    __tablename__ = "teachers"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    submissions = relationship("Submission", back_populates="teacher")
    
    @classmethod
    async def get_by_telegram_id(cls, session, telegram_id):
        """Get teacher by telegram ID"""
        return await session.query(cls).filter(cls.telegram_id == telegram_id).first()
    
    def __repr__(self):
        return f"<Teacher {self.full_name}>"

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True)
    django_id = Column(Integer, unique=True, nullable=False)  # User ID in Django
    telegram_id = Column(Integer, unique=True, nullable=True)  # Can be null if not connected
    full_name = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    submissions = relationship("Submission", back_populates="student")
    
    @classmethod
    async def get_by_telegram_id(cls, session, telegram_id):
        """Get student by telegram ID"""
        return await session.query(cls).filter(cls.telegram_id == telegram_id).first()
    
    @classmethod
    async def get_by_django_id(cls, session, django_id):
        """Get student by Django ID"""
        return await session.query(cls).filter(cls.django_id == django_id).first()
    
    def __repr__(self):
        return f"<Student {self.full_name}>"

class Submission(Base):
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True)
    django_id = Column(Integer, unique=True, nullable=False)  # TestResult ID in Django
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    section = Column(String(20), nullable=False)  # 'writing' or 'speaking'
    text = Column(Text, nullable=True)  # For writing submissions
    audio_path = Column(String(255), nullable=True)  # For speaking submissions
    status = Column(String(20), default="pending")  # pending, checking, completed
    score = Column(Integer, nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    
    # Relationships
    student = relationship("Student", back_populates="submissions")
    teacher = relationship("Teacher", back_populates="submissions")
    
    @property
    async def get_student(self):
        """Get student for this submission asynchronously"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        
        async with async_session() as session:
            query = select(Student).where(Student.id == self.student_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @property
    async def get_teacher(self):
        """Get teacher for this submission asynchronously"""
        if not self.teacher_id:
            return None
            
        from sqlalchemy import select
        
        async with async_session() as session:
            query = select(Teacher).where(Teacher.id == self.teacher_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    def __repr__(self):
        return f"<Submission {self.id}: {self.section}>"

# Initialize database
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
# Get session
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

# CRUD operations
class DatabaseManager:
    @staticmethod
    async def get_pending_submissions(session):
        """Get all pending submissions"""
        query = (
            session.query(Submission)
            .filter(Submission.status == "pending")
            .order_by(Submission.created_at.asc())
        )
        return await query.all()
    
    @staticmethod
    async def update_submission_status(session, submission_id, status, teacher_id=None):
        """Update submission status"""
        submission = await session.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = status
            if teacher_id:
                submission.teacher_id = teacher_id
            await session.commit()
            return submission
        return None
    
    @staticmethod
    async def update_submission_score(session, submission_id, score, feedback, teacher_id):
        """Update submission score and feedback"""
        submission = await session.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.score = score
            submission.feedback = feedback
            submission.teacher_id = teacher_id
            submission.status = "completed"
            await session.commit()
            return submission
        return None
    
    @staticmethod
    async def get_teacher_by_telegram_id(session, telegram_id):
        """Get teacher by telegram ID"""
        return await session.query(Teacher).filter(Teacher.telegram_id == telegram_id).first()
    
    @staticmethod
    async def get_student_by_django_id(session, django_id):
        """Get student by Django ID"""
        return await session.query(Student).filter(Student.django_id == django_id).first()
    
    @staticmethod
    async def create_submission(session, django_id, student_id, section, text=None, audio_path=None):
        """Create a new submission"""
        submission = Submission(
            django_id=django_id,
            student_id=student_id,
            section=section,
            text=text,
            audio_path=audio_path
        )
        session.add(submission)
        await session.commit()
        return submission
