"""Tests for Phase 6 API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock


@pytest.fixture
def client():
    """Create test client."""
    from backend.app.main import app
    return TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"

    def test_health_endpoint(self, client):
        """Test health check."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestProfileAPI:
    """Test profile API endpoints."""

    @patch('backend.app.api.profile.SessionLocal')
    def test_get_profile(self, mock_session, client):
        """Test get profile."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_profile = Mock(
            id=1,
            name="John Doe",
            email="john@example.com",
            phone="+1-555-0100",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/johndoe",
            github_url=None,
            portfolio_url=None,
            work_authorization="US Citizen"
        )
        mock_db.query().filter().first.return_value = mock_profile

        response = client.get("/api/profile?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"

    @patch('backend.app.api.profile.SessionLocal')
    def test_get_profile_not_found(self, mock_session, client):
        """Test get profile not found."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query().filter().first.return_value = None

        response = client.get("/api/profile?user_id=999")
        assert response.status_code == 404

    @patch('backend.app.api.profile.SessionLocal')
    def test_get_skills(self, mock_session, client):
        """Test get skills."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_skills = [
            Mock(id=1, name="Python", proficiency="Expert", category="Programming"),
            Mock(id=2, name="AWS", proficiency="Advanced", category="Cloud"),
        ]
        mock_db.query().filter().all.return_value = mock_skills

        response = client.get("/api/profile/skills?user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Python"


class TestJobsAPI:
    """Test jobs API endpoints."""

    @patch('backend.app.api.jobs.SessionLocal')
    def test_list_jobs(self, mock_session, client):
        """Test list jobs."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import datetime
        mock_jobs = [
            Mock(
                id=1,
                platform="linkedin",
                company="Google",
                title="Software Engineer",
                location="Mountain View, CA",
                job_url="https://example.com/job1",
                description="Build cool stuff",
                requirements=None,
                salary_range="$120k-$180k",
                posted_date=datetime(2026, 6, 1),
                status="discovered",
                match_score=0.85,
                created_at=datetime(2026, 6, 7)
            )
        ]
        mock_db.query().order_by().offset().limit().all.return_value = mock_jobs

        response = client.get("/api/jobs?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["company"] == "Google"

    @patch('backend.app.api.jobs.SessionLocal')
    def test_get_job(self, mock_session, client):
        """Test get job details."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import datetime
        mock_job = Mock(
            id=1,
            platform="linkedin",
            company="Google",
            title="Software Engineer",
            location="Mountain View, CA",
            job_url="https://example.com/job1",
            description="Build cool stuff",
            requirements=None,
            salary_range="$120k-$180k",
            posted_date=datetime(2026, 6, 1),
            status="discovered",
            match_score=0.85,
            created_at=datetime(2026, 6, 7)
        )
        mock_db.query().filter().first.return_value = mock_job

        response = client.get("/api/jobs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["company"] == "Google"
        assert data["match_score"] == 0.85

    @patch('backend.app.api.jobs.SessionLocal')
    def test_add_to_queue(self, mock_session, client):
        """Test add job to queue."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(id=1, match_score=0.85)
        mock_db.query().filter().first.side_effect = [mock_job, None]  # job exists, not in queue

        response = client.post("/api/jobs/queue/add", json={"job_id": 1, "priority": 8})
        assert response.status_code == 200
        data = response.json()
        assert "queue_id" in data


class TestApplicationsAPI:
    """Test applications API endpoints."""

    @patch('backend.app.api.applications.SessionLocal')
    def test_get_stats(self, mock_session, client):
        """Test get application statistics."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        # Mock counts
        mock_db.query().count.side_effect = [100, 75, 5, 20]  # total, submitted, pending, failed
        mock_db.query().filter().count.side_effect = [15, 67]  # today, this week

        response = client.get("/api/applications/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert data["total_applications"] == 100
        assert data["submitted"] == 75
        assert data["pending_questions"] == 5
        assert data["failed"] == 20
        assert data["success_rate"] == 75.0

    @patch('backend.app.api.applications.SessionLocal')
    def test_get_daily_stats(self, mock_session, client):
        """Test get daily statistics."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import date
        mock_stats = [
            Mock(
                date=date(2026, 6, 1),
                applications_submitted=10,
                applications_failed=2,
                avg_success_rate=0.83
            ),
            Mock(
                date=date(2026, 6, 2),
                applications_submitted=15,
                applications_failed=1,
                avg_success_rate=0.94
            ),
        ]
        mock_db.query().filter().order_by().all.return_value = mock_stats

        response = client.get("/api/applications/stats/daily?days=30")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["applications_submitted"] == 10


class TestDaemonAPI:
    """Test daemon API endpoints."""

    @patch('backend.app.api.daemon.SessionLocal')
    def test_get_status_running(self, mock_session, client):
        """Test get daemon status when running."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import datetime
        mock_state = Mock(
            is_running=True,
            config_id=1,
            applications_today=15,
            queue_size=23,
            last_cycle_at=datetime(2026, 6, 7, 15, 45, 23)
        )
        mock_config = Mock(
            id=1,
            search_criteria="Senior Software Engineer",
            max_applications_per_day=50
        )
        mock_db.query().first.side_effect = [mock_state, mock_config]

        response = client.get("/api/daemon/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is True
        assert data["applications_today"] == 15
        assert data["queue_size"] == 23

    @patch('backend.app.api.daemon.SessionLocal')
    def test_get_status_stopped(self, mock_session, client):
        """Test get daemon status when stopped."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db
        mock_db.query().first.return_value = None

        response = client.get("/api/daemon/status")
        assert response.status_code == 200
        data = response.json()
        assert data["is_running"] is False

    @patch('backend.app.api.daemon.SessionLocal')
    def test_get_logs(self, mock_session, client):
        """Test get daemon logs."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import datetime
        mock_logs = [
            Mock(
                id=1,
                timestamp=datetime(2026, 6, 7, 15, 45, 23),
                level="INFO",
                message="Cycle complete",
                details=None
            ),
            Mock(
                id=2,
                timestamp=datetime(2026, 6, 7, 15, 45, 20),
                level="ERROR",
                message="Application failed",
                details='{"job_id": 123}'
            ),
        ]
        mock_db.query().order_by().limit().all.return_value = mock_logs

        response = client.get("/api/daemon/logs?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["level"] == "INFO"


class TestQuestionsAPI:
    """Test questions and AI API endpoints."""

    @patch('backend.app.api.questions.SessionLocal')
    def test_list_pending_questions(self, mock_session, client):
        """Test list pending questions."""
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        from datetime import datetime
        mock_questions = [
            Mock(
                id=1,
                application_id=10,
                job_id=5,
                question_text="Are you willing to relocate?",
                field_type="yes_no",
                status="pending",
                created_at=datetime(2026, 6, 7, 14, 30)
            )
        ]
        mock_job = Mock(
            company="Google",
            title="Software Engineer",
            platform="linkedin"
        )
        mock_db.query().filter().order_by().limit().all.return_value = mock_questions
        mock_db.query().filter().first.return_value = mock_job

        response = client.get("/api/questions/pending?status=pending&limit=50")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["question_text"] == "Are you willing to relocate?"

    @patch('backend.app.api.questions.QuestionService')
    def test_answer_question(self, mock_qs, client):
        """Test answer question."""
        mock_qs_instance = MagicMock()
        mock_qs.return_value.__enter__.return_value = mock_qs_instance

        mock_question = Mock(id=1)
        mock_qs_instance.answer_question.return_value = mock_question

        response = client.post("/api/questions/answer", json={
            "question_id": 1,
            "answer": "Yes",
            "save_to_kb": True,
            "reuse_policy": "always_same"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["question_id"] == 1

    @patch('backend.app.api.questions.AIService')
    def test_get_ai_suggestion(self, mock_ai_service, client):
        """Test get AI suggestion."""
        mock_ai_instance = Mock()
        mock_ai_instance.suggest_answer.return_value = "Yes, I am willing to relocate"
        mock_ai_service.return_value = mock_ai_instance

        response = client.post("/api/questions/suggest", json={
            "question_text": "Are you willing to relocate?",
            "job_id": 1,
            "field_type": "yes_no"
        })
        assert response.status_code == 200
        data = response.json()
        assert "relocate" in data["suggestion"].lower()

    @patch('backend.app.api.questions.AIService')
    def test_generate_cover_letter(self, mock_ai_service, client):
        """Test generate cover letter."""
        mock_ai_instance = Mock()
        mock_ai_instance.generate_cover_letter.return_value = "Dear Hiring Manager..."
        mock_ai_service.return_value = mock_ai_instance

        response = client.post("/api/questions/ai/cover-letter", json={
            "job_id": 1,
            "user_id": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert "cover_letter" in data
        assert data["cover_letter"].startswith("Dear")

    @patch('backend.app.api.questions.AIService')
    def test_calculate_match_score(self, mock_ai_service, client):
        """Test calculate match score."""
        mock_ai_instance = Mock()
        mock_ai_instance.calculate_job_match.return_value = {
            "match_score": 0.85,
            "matching_skills": ["Python", "AWS"],
            "missing_skills": ["Kubernetes"],
            "recommendation": "apply"
        }
        mock_ai_service.return_value = mock_ai_instance

        response = client.post("/api/questions/ai/match-score?job_id=1&user_id=1")
        assert response.status_code == 200
        data = response.json()
        assert data["match_score"] == 0.85
        assert data["recommendation"] == "apply"


class TestCORS:
    """Test CORS configuration."""

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/api/health",
            headers={"Origin": "http://localhost:5173"}
        )
        # CORS middleware should add headers
        assert response.status_code in [200, 204]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
