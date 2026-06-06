"""Service for managing pending questions."""
import json
from datetime import datetime
from typing import Dict, List, Optional

from backend.app.database.session import SessionLocal
from backend.app.models import Application, PendingQuestion
from backend.app.services.knowledge_base import KnowledgeBaseService


class QuestionService:
    """Manage pending questions and answers."""

    def __init__(self):
        """Initialize question service."""
        self.db = SessionLocal()
        self.kb_service = KnowledgeBaseService()

    def create_question(
        self,
        application_id: int,
        job_id: int,
        question_text: str,
        field_type: str,
        field_selector: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> PendingQuestion:
        """
        Create a new pending question.

        Args:
            application_id: Application ID
            job_id: Job ID
            question_text: Question text
            field_type: Field type (text, dropdown, number, yes_no, multiline)
            field_selector: CSS selector for the field
            context: Additional context

        Returns:
            Created PendingQuestion
        """
        question = PendingQuestion(
            application_id=application_id,
            job_id=job_id,
            question_text=question_text,
            field_type=field_type,
            field_selector=field_selector,
            context=json.dumps(context) if context else None,
            status="pending",
        )

        self.db.add(question)
        self.db.commit()

        # Update application status to pending_questions
        app = (
            self.db.query(Application)
            .filter(Application.id == application_id)
            .first()
        )

        if app and app.status == "processing":
            app.status = "pending_questions"
            self.db.commit()

        return question

    def get_pending_questions(
        self,
        application_id: Optional[int] = None,
        status: str = "pending",
    ) -> List[PendingQuestion]:
        """
        Get pending questions.

        Args:
            application_id: Filter by application ID
            status: Filter by status

        Returns:
            List of pending questions
        """
        query = self.db.query(PendingQuestion).filter(
            PendingQuestion.status == status
        )

        if application_id:
            query = query.filter(PendingQuestion.application_id == application_id)

        return query.order_by(PendingQuestion.created_at.asc()).all()

    def answer_question(
        self,
        question_id: int,
        answer: str,
        save_to_kb: bool = True,
        reuse_policy: str = "always_same",
    ) -> PendingQuestion:
        """
        Answer a pending question.

        Args:
            question_id: Question ID
            answer: User's answer
            save_to_kb: Save to knowledge base
            reuse_policy: How to reuse answer

        Returns:
            Updated PendingQuestion
        """
        question = (
            self.db.query(PendingQuestion)
            .filter(PendingQuestion.id == question_id)
            .first()
        )

        if not question:
            raise ValueError(f"Question {question_id} not found")

        # Save answer
        question.user_answer = answer
        question.status = "answered"
        question.answered_at = datetime.utcnow()

        self.db.commit()

        # Save to knowledge base
        if save_to_kb:
            context = json.loads(question.context) if question.context else {}
            self.kb_service.add_answer(
                question_text=question.question_text,
                answer=answer,
                reuse_policy=reuse_policy,
                context=context,
            )

        return question

    def batch_answer_questions(
        self,
        answers: Dict[int, str],
        save_to_kb: bool = True,
        reuse_policy: str = "always_same",
    ) -> int:
        """
        Answer multiple questions at once.

        Args:
            answers: Dictionary of {question_id: answer}
            save_to_kb: Save answers to knowledge base
            reuse_policy: How to reuse answers

        Returns:
            Number of questions answered
        """
        count = 0

        for question_id, answer in answers.items():
            try:
                self.answer_question(question_id, answer, save_to_kb, reuse_policy)
                count += 1
            except Exception as e:
                print(f"Error answering question {question_id}: {e}")

        return count

    def skip_question(self, question_id: int):
        """Mark question as skipped."""
        question = (
            self.db.query(PendingQuestion)
            .filter(PendingQuestion.id == question_id)
            .first()
        )

        if question:
            question.status = "skipped"
            self.db.commit()

    def check_applications_ready_to_resume(self) -> List[int]:
        """
        Check which applications have all questions answered.

        Returns:
            List of application IDs ready to resume
        """
        # Get all applications in pending_questions status
        pending_apps = (
            self.db.query(Application)
            .filter(Application.status == "pending_questions")
            .all()
        )

        ready_apps = []

        for app in pending_apps:
            # Check if all questions are answered
            unanswered = (
                self.db.query(PendingQuestion)
                .filter(
                    PendingQuestion.application_id == app.id,
                    PendingQuestion.status == "pending",
                )
                .count()
            )

            if unanswered == 0:
                ready_apps.append(app.id)

        return ready_apps

    def get_answered_questions_for_application(
        self, application_id: int
    ) -> List[PendingQuestion]:
        """Get all answered questions for an application."""
        return (
            self.db.query(PendingQuestion)
            .filter(
                PendingQuestion.application_id == application_id,
                PendingQuestion.status == "answered",
            )
            .all()
        )

    def auto_answer_from_knowledge_base(
        self,
        question_text: str,
        field_type: str,
        context: Optional[Dict] = None,
        min_confidence: float = 0.8,
    ) -> Optional[str]:
        """
        Try to automatically answer a question from knowledge base.

        Args:
            question_text: Question text
            field_type: Field type
            context: Optional context
            min_confidence: Minimum confidence threshold

        Returns:
            Answer if found with sufficient confidence, None otherwise
        """
        result = self.kb_service.find_similar_answer(
            question_text=question_text,
            context=context,
            min_confidence=min_confidence,
        )

        if result and result["reuse_policy"] != "always_ask":
            return result["answer"]

        return None

    def get_question_statistics(self) -> Dict:
        """Get statistics about questions."""
        total_pending = (
            self.db.query(PendingQuestion)
            .filter(PendingQuestion.status == "pending")
            .count()
        )

        total_answered = (
            self.db.query(PendingQuestion)
            .filter(PendingQuestion.status == "answered")
            .count()
        )

        total_skipped = (
            self.db.query(PendingQuestion)
            .filter(PendingQuestion.status == "skipped")
            .count()
        )

        # Get most common questions
        from sqlalchemy import func

        common_questions = (
            self.db.query(
                PendingQuestion.question_text,
                func.count(PendingQuestion.id).label("count"),
            )
            .group_by(PendingQuestion.question_text)
            .order_by(func.count(PendingQuestion.id).desc())
            .limit(5)
            .all()
        )

        return {
            "total_pending": total_pending,
            "total_answered": total_answered,
            "total_skipped": total_skipped,
            "answer_rate": (
                round(total_answered / (total_answered + total_skipped) * 100, 1)
                if (total_answered + total_skipped) > 0
                else 0
            ),
            "common_questions": [
                {"question": q[0], "count": q[1]} for q in common_questions
            ],
        }

    def close(self):
        """Close database connections."""
        self.kb_service.close()
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
