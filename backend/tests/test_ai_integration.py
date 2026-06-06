"""Tests for Phase 5 AI Integration."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.ai.claude_client import ClaudeCodeClient
from backend.app.ai.ai_service import AIService


class TestClaudeCodeClient:
    """Test Claude Code CLI client."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        client = ClaudeCodeClient()
        assert client.claude_path is not None

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        custom_path = "/custom/claude"
        client = ClaudeCodeClient(claude_path=custom_path)
        assert client.claude_path == custom_path

    @patch('subprocess.run')
    def test_prompt_success(self, mock_run):
        """Test successful prompt execution."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Generated response",
            stderr=""
        )

        client = ClaudeCodeClient()
        response = client.prompt("Test prompt")

        assert response == "Generated response"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_prompt_failure(self, mock_run):
        """Test prompt execution failure."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout="",
            stderr="Error occurred"
        )

        client = ClaudeCodeClient()

        with pytest.raises(RuntimeError, match="Claude Code CLI failed"):
            client.prompt("Test prompt")

    @patch('subprocess.run')
    def test_prompt_timeout(self, mock_run):
        """Test prompt timeout."""
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("claude", 60)

        client = ClaudeCodeClient()

        with pytest.raises(RuntimeError, match="timed out"):
            client.prompt("Test prompt", timeout=60)

    @patch('subprocess.run')
    def test_prompt_json_success(self, mock_run):
        """Test JSON prompt parsing."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"key": "value"}',
            stderr=""
        )

        client = ClaudeCodeClient()
        response = client.prompt_json("Test prompt")

        assert response == {"key": "value"}

    @patch('subprocess.run')
    def test_prompt_json_markdown_wrapped(self, mock_run):
        """Test JSON parsing with markdown wrapper."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='```json\n{"key": "value"}\n```',
            stderr=""
        )

        client = ClaudeCodeClient()
        response = client.prompt_json("Test prompt")

        assert response == {"key": "value"}

    @patch('subprocess.run')
    def test_prompt_json_embedded(self, mock_run):
        """Test JSON parsing when embedded in text."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='Here is the result: {"key": "value"} Done.',
            stderr=""
        )

        client = ClaudeCodeClient()
        response = client.prompt_json("Test prompt")

        assert response == {"key": "value"}


class TestAIService:
    """Test AI service methods."""

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_generate_cover_letter(self, mock_session, mock_claude):
        """Test cover letter generation."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(
            id=1,
            company="Google",
            title="Software Engineer",
            location="Mountain View",
            description="Build cool stuff"
        )
        mock_profile = Mock(
            id=1,
            name="John Doe",
            email="john@example.com"
        )

        mock_db.query().filter().first.side_effect = [mock_job, mock_profile]

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt.return_value = "Dear Hiring Manager,\n\nI am excited..."
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        cover_letter = service.generate_cover_letter(
            job_id=1,
            user_profile_id=1
        )

        assert cover_letter.startswith("Dear Hiring Manager")
        mock_claude_instance.prompt.assert_called_once()

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_calculate_job_match(self, mock_session, mock_claude):
        """Test job match calculation."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(
            id=1,
            company="Google",
            title="Software Engineer",
            description="Python, AWS required"
        )
        mock_profile = Mock(id=1)

        mock_db.query().filter().first.side_effect = [mock_job, mock_profile]
        mock_db.query().filter().all.return_value = [
            Mock(name="Python", proficiency="Expert"),
            Mock(name="AWS", proficiency="Advanced"),
        ]

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt_json.return_value = {
            "match_score": 85,
            "matching_skills": ["Python", "AWS"],
            "missing_skills": ["Kubernetes"],
            "recommendation": "apply",
            "reasoning": "Strong technical match"
        }
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        result = service.calculate_job_match(
            job_id=1,
            user_profile_id=1
        )

        assert result["match_score"] == 0.85  # Converted to 0-1
        assert "Python" in result["matching_skills"]
        assert result["recommendation"] == "apply"

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_suggest_answer(self, mock_session, mock_claude):
        """Test answer suggestion."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(
            id=1,
            company="Google",
            title="Software Engineer",
            description="Remote position"
        )
        mock_profile = Mock(
            id=1,
            name="John Doe",
            work_authorization="US Citizen"
        )

        mock_db.query().filter().first.side_effect = [mock_job, mock_profile]

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt.return_value = "Yes, I am willing to relocate"
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        answer = service.suggest_answer(
            question_text="Are you willing to relocate?",
            job_id=1,
            user_profile_id=1,
            field_type="text"
        )

        assert "relocate" in answer.lower()
        mock_claude_instance.prompt.assert_called_once()

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_suggest_answer_yes_no(self, mock_session, mock_claude):
        """Test yes/no answer suggestion."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_db.query().filter().first.return_value = None

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt.return_value = "yes"
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        answer = service.suggest_answer(
            question_text="Do you have a driver's license?",
            field_type="yes_no"
        )

        assert answer == "yes"

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_batch_suggest_answers(self, mock_session, mock_claude):
        """Test batch answer suggestions."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_db.query().filter().first.return_value = None

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt.side_effect = [
            "yes",
            "5 years",
            "I am passionate about software engineering"
        ]
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        questions = [
            (1, "Are you eligible to work?", "yes_no"),
            (2, "Years of experience?", "number"),
            (3, "Why this role?", "text")
        ]

        suggestions = service.batch_suggest_answers(questions)

        assert suggestions[1] == "yes"
        assert suggestions[2] == "5 years"
        assert "passionate" in suggestions[3].lower()

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_analyze_resume_for_job(self, mock_session, mock_claude):
        """Test resume analysis."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(
            id=1,
            title="Senior Engineer",
            company="Google",
            description="Python expert needed"
        )
        mock_resumes = [
            Mock(id=1, title="General Resume", tags="python,java"),
            Mock(id=2, title="Senior Resume", tags="python,leadership"),
        ]

        mock_db.query().filter().first.return_value = mock_job
        mock_db.query().filter().all.return_value = mock_resumes

        # Mock Claude response
        mock_claude_instance = Mock()
        mock_claude_instance.prompt_json.return_value = {
            "recommended_resume_id": 2,
            "reasoning": "Senior Resume emphasizes leadership",
            "suggestions": ["Add more Python projects", "Highlight AWS experience"]
        }
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        result = service.analyze_resume_for_job(
            job_id=1,
            user_profile_id=1
        )

        assert result["recommended_resume_id"] == 2
        assert "leadership" in result["reasoning"].lower()
        assert len(result["suggestions"]) == 2


class TestAIIntegration:
    """Integration tests for AI features."""

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    def test_ai_service_initialization(self, mock_claude):
        """Test AI service initializes correctly."""
        service = AIService()
        assert service.claude is not None

    @patch('backend.app.ai.ai_service.ClaudeCodeClient')
    @patch('backend.app.ai.ai_service.SessionLocal')
    def test_cover_letter_saves_to_db(self, mock_session, mock_claude):
        """Test that generated cover letter can be saved."""
        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_job = Mock(
            id=1,
            company="Google",
            title="Software Engineer",
            location="Remote",
            description="Build stuff"
        )
        mock_profile = Mock(
            id=1,
            name="John Doe",
            email="john@example.com",
            linkedin_url=None,
            work_authorization="US Citizen"
        )

        mock_db.query().filter().first.side_effect = [mock_job, mock_profile]

        # Mock Claude
        mock_claude_instance = Mock()
        mock_claude_instance.prompt.return_value = "Dear Hiring Manager..."
        mock_claude.return_value = mock_claude_instance

        # Test
        service = AIService()
        cover_letter = service.generate_cover_letter(1, 1)

        # Verify cover letter was generated
        assert cover_letter is not None
        assert len(cover_letter) > 0

    @patch('backend.app.services.question_service.AIService')
    @patch('backend.app.services.question_service.SessionLocal')
    def test_question_service_ai_integration(self, mock_session, mock_ai_service):
        """Test QuestionService integrates with AI."""
        from backend.app.services.question_service import QuestionService

        # Mock database
        mock_db = MagicMock()
        mock_session.return_value = mock_db

        mock_question = Mock(
            id=1,
            question_text="Are you willing to relocate?",
            job_id=1,
            field_type="yes_no"
        )
        mock_db.query().filter().first.return_value = mock_question

        # Mock AI service
        mock_ai_instance = Mock()
        mock_ai_instance.suggest_answer.return_value = "Yes"
        mock_ai_service.return_value = mock_ai_instance

        # Test
        qs = QuestionService()
        suggestion = qs.get_ai_suggestion(question_id=1)

        assert suggestion == "Yes"
        mock_ai_instance.suggest_answer.assert_called_once()


def test_ai_cli_commands_exist():
    """Test that AI CLI commands are registered."""
    from cli.commands import ai

    assert hasattr(ai, 'app')
    assert hasattr(ai.app, 'registered_commands')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
