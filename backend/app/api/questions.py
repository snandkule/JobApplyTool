"""Questions and AI API endpoints."""
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.ai.ai_service import AIService
from backend.app.database.session import SessionLocal
from backend.app.models import Job, KnowledgeBase, PendingQuestion
from backend.app.services.knowledge_base import KnowledgeBaseService
from backend.app.services.question_service import QuestionService

router = APIRouter()


class PendingQuestionResponse(BaseModel):
    id: int
    application_id: int
    job_id: int
    question_text: str
    field_type: str
    status: str
    created_at: str
    job: Optional[dict] = None

    class Config:
        from_attributes = True


class AnswerQuestionRequest(BaseModel):
    question_id: int
    answer: str
    save_to_kb: bool = True
    reuse_policy: str = "always_same"


class BatchAnswerRequest(BaseModel):
    answers: Dict[int, str]
    save_to_kb: bool = True
    reuse_policy: str = "always_same"


class AISuggestionRequest(BaseModel):
    question_text: str
    job_id: Optional[int] = None
    field_type: str = "text"


class GenerateCoverLetterRequest(BaseModel):
    job_id: int
    user_id: int = 1


@router.get("/pending", response_model=List[PendingQuestionResponse])
async def list_pending_questions(
    status: str = "pending",
    limit: int = 50,
):
    """List pending questions."""
    db = SessionLocal()
    try:
        questions = (
            db.query(PendingQuestion)
            .filter(PendingQuestion.status == status)
            .order_by(PendingQuestion.created_at.asc())
            .limit(limit)
            .all()
        )

        result = []
        for q in questions:
            job = db.query(Job).filter(Job.id == q.job_id).first()
            result.append({
                "id": q.id,
                "application_id": q.application_id,
                "job_id": q.job_id,
                "question_text": q.question_text,
                "field_type": q.field_type,
                "status": q.status,
                "created_at": q.created_at.isoformat(),
                "job": {
                    "company": job.company,
                    "title": job.title,
                    "platform": job.platform,
                } if job else None,
            })

        return result
    finally:
        db.close()


@router.post("/answer")
async def answer_question(request: AnswerQuestionRequest):
    """Answer a pending question."""
    with QuestionService() as qs:
        try:
            question = qs.answer_question(
                question_id=request.question_id,
                answer=request.answer,
                save_to_kb=request.save_to_kb,
                reuse_policy=request.reuse_policy,
            )
            return {
                "message": "Question answered",
                "question_id": question.id,
                "saved_to_kb": request.save_to_kb,
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-answer")
async def batch_answer_questions(request: BatchAnswerRequest):
    """Answer multiple questions at once."""
    with QuestionService() as qs:
        try:
            count = qs.batch_answer_questions(
                answers=request.answers,
                save_to_kb=request.save_to_kb,
                reuse_policy=request.reuse_policy,
            )
            return {
                "message": f"Answered {count} questions",
                "count": count,
                "saved_to_kb": request.save_to_kb,
            }
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/suggest")
async def get_ai_suggestion(request: AISuggestionRequest):
    """Get AI suggestion for a question."""
    try:
        ai = AIService()
        suggestion = ai.suggest_answer(
            question_text=request.question_text,
            job_id=request.job_id,
            user_profile_id=1,
            field_type=request.field_type,
        )
        return {"suggestion": suggestion}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI suggestion failed: {str(e)}")


@router.get("/knowledge-base")
async def list_knowledge_base(limit: int = 100):
    """List knowledge base entries."""
    db = SessionLocal()
    try:
        entries = (
            db.query(KnowledgeBase)
            .order_by(KnowledgeBase.usage_count.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": entry.id,
                "question_normalized": entry.question_normalized,
                "answer": entry.answer,
                "reuse_policy": entry.reuse_policy,
                "usage_count": entry.usage_count,
                "confidence": entry.confidence,
                "last_used": (
                    entry.last_used.isoformat() if entry.last_used else None
                ),
            }
            for entry in entries
        ]
    finally:
        db.close()


@router.get("/stats")
async def get_question_stats():
    """Get question statistics."""
    with QuestionService() as qs:
        return qs.get_question_statistics()


@router.post("/ai/cover-letter")
async def generate_cover_letter(request: GenerateCoverLetterRequest):
    """Generate AI cover letter for a job."""
    try:
        ai = AIService()
        cover_letter = ai.generate_cover_letter(
            job_id=request.job_id,
            user_profile_id=request.user_id,
        )
        return {"cover_letter": cover_letter}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Cover letter generation failed: {str(e)}"
        )


@router.post("/ai/match-score")
async def calculate_match_score(job_id: int, user_id: int = 1):
    """Calculate AI match score for a job."""
    try:
        ai = AIService()
        result = ai.calculate_job_match(
            job_id=job_id,
            user_profile_id=user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Match scoring failed: {str(e)}"
        )


@router.post("/ai/analyze-resume")
async def analyze_resume(job_id: int, user_id: int = 1):
    """Analyze which resume to use for a job."""
    try:
        ai = AIService()
        result = ai.analyze_resume_for_job(
            job_id=job_id,
            user_profile_id=user_id,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Resume analysis failed: {str(e)}"
        )
