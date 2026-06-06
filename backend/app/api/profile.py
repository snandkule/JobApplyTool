"""Profile management API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.database.session import SessionLocal
from backend.app.models import Education, Resume, Skill, UserProfile, WorkHistory

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    work_authorization: Optional[str]

    class Config:
        from_attributes = True


class SkillResponse(BaseModel):
    id: int
    name: str
    proficiency: Optional[str]
    category: Optional[str]

    class Config:
        from_attributes = True


class ResumeResponse(BaseModel):
    id: int
    file_name: str
    title: Optional[str]
    file_path: str
    is_default: bool
    tags: Optional[str]

    class Config:
        from_attributes = True


class WorkHistoryResponse(BaseModel):
    id: int
    company: str
    title: str
    start_date: str
    end_date: Optional[str]
    description: Optional[str]
    location: Optional[str]

    class Config:
        from_attributes = True


class EducationResponse(BaseModel):
    id: int
    institution: str
    degree: str
    field_of_study: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    gpa: Optional[float]

    class Config:
        from_attributes = True


@router.get("/", response_model=UserProfileResponse)
async def get_profile(user_id: int = 1):
    """Get user profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile
    finally:
        db.close()


@router.post("/", response_model=UserProfileResponse)
async def create_profile(
    name: str,
    email: str,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    portfolio_url: Optional[str] = None,
    work_authorization: Optional[str] = None,
):
    """Create new user profile."""
    db = SessionLocal()
    try:
        profile = UserProfile(
            name=name,
            email=email,
            phone=phone,
            location=location,
            linkedin_url=linkedin_url,
            github_url=github_url,
            portfolio_url=portfolio_url,
            work_authorization=work_authorization,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile
    finally:
        db.close()


@router.put("/", response_model=UserProfileResponse)
async def update_profile(
    user_id: int = 1,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    location: Optional[str] = None,
    linkedin_url: Optional[str] = None,
    github_url: Optional[str] = None,
    portfolio_url: Optional[str] = None,
    work_authorization: Optional[str] = None,
):
    """Update user profile."""
    db = SessionLocal()
    try:
        profile = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        if name:
            profile.name = name
        if email:
            profile.email = email
        if phone:
            profile.phone = phone
        if location:
            profile.location = location
        if linkedin_url:
            profile.linkedin_url = linkedin_url
        if github_url:
            profile.github_url = github_url
        if portfolio_url:
            profile.portfolio_url = portfolio_url
        if work_authorization:
            profile.work_authorization = work_authorization

        db.commit()
        db.refresh(profile)
        return profile
    finally:
        db.close()


@router.get("/skills", response_model=List[SkillResponse])
async def get_skills(user_id: int = 1):
    """Get user skills."""
    db = SessionLocal()
    try:
        skills = db.query(Skill).filter(Skill.user_id == user_id).all()
        return skills
    finally:
        db.close()


@router.post("/skills", response_model=SkillResponse)
async def add_skill(
    name: str,
    user_id: int = 1,
    proficiency: Optional[str] = None,
    category: Optional[str] = None,
):
    """Add skill to profile."""
    db = SessionLocal()
    try:
        skill = Skill(
            user_id=user_id,
            name=name,
            proficiency=proficiency,
            category=category,
        )
        db.add(skill)
        db.commit()
        db.refresh(skill)
        return skill
    finally:
        db.close()


@router.get("/resumes", response_model=List[ResumeResponse])
async def get_resumes(user_id: int = 1):
    """Get user resumes."""
    db = SessionLocal()
    try:
        resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
        return resumes
    finally:
        db.close()


@router.get("/work-history", response_model=List[WorkHistoryResponse])
async def get_work_history(user_id: int = 1):
    """Get work history."""
    db = SessionLocal()
    try:
        history = db.query(WorkHistory).filter(WorkHistory.user_id == user_id).all()
        return history
    finally:
        db.close()


@router.get("/education", response_model=List[EducationResponse])
async def get_education(user_id: int = 1):
    """Get education history."""
    db = SessionLocal()
    try:
        education = db.query(Education).filter(Education.user_id == user_id).all()
        return education
    finally:
        db.close()
