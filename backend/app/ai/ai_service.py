"""AI services for job applications using Claude Code CLI."""
from typing import Dict, Optional

from backend.app.ai.claude_client import ClaudeCodeClient
from backend.app.database.session import SessionLocal
from backend.app.models import Job, UserProfile


class AIService:
    """AI-powered services for job applications."""

    def __init__(self):
        """Initialize AI service."""
        self.claude = ClaudeCodeClient()

    def generate_cover_letter(
        self,
        job_id: int,
        user_profile_id: int,
        max_words: int = 400,
    ) -> str:
        """
        Generate tailored cover letter for job.

        Args:
            job_id: Job database ID
            user_profile_id: User profile ID
            max_words: Maximum word count

        Returns:
            Generated cover letter text
        """
        db = SessionLocal()

        try:
            # Get job and profile
            job = db.query(Job).filter(Job.id == job_id).first()
            profile = db.query(UserProfile).filter(UserProfile.id == user_profile_id).first()

            if not job or not profile:
                raise ValueError("Job or profile not found")

            # Get resume content if available
            from backend.app.models import Resume
            import json

            resume_content = ""
            resume = db.query(Resume).filter(
                Resume.user_id == user_profile_id,
                Resume.is_default == True
            ).first()

            if resume and resume.parsed_content:
                try:
                    parsed = json.loads(resume.parsed_content)

                    # Extract key information from parsed resume
                    resume_parts = []

                    if parsed.get('sections', {}).get('experience'):
                        resume_parts.append(f"Experience:\n{parsed['sections']['experience'][:500]}")

                    if parsed.get('sections', {}).get('skills'):
                        resume_parts.append(f"Skills:\n{parsed['sections']['skills'][:300]}")

                    if parsed.get('skills'):
                        resume_parts.append(f"Technical Skills: {', '.join(parsed['skills'][:15])}")

                    resume_content = "\n\n".join(resume_parts)
                except:
                    pass

            # Get skills from database
            from backend.app.models import Skill
            skills = db.query(Skill).filter(Skill.user_id == user_profile_id).all()
            skills_text = ", ".join([s.name for s in skills]) if skills else ""

            # Build prompt
            prompt = f"""Generate a professional cover letter for the following job application.

Job Details:
- Company: {job.company}
- Title: {job.title}
- Location: {job.location}
- Description: {job.description or 'Not provided'}

Candidate Profile:
- Name: {profile.name}
- Email: {profile.email}
- LinkedIn: {profile.linkedin_url or 'Not provided'}
- Work Authorization: {profile.work_authorization or 'Not specified'}
- Skills: {skills_text}

{f"Resume Content:\n{resume_content}\n" if resume_content else ""}

Requirements:
1. Tailor the letter specifically to this job and company
2. Highlight relevant experience and skills from the resume
3. Professional and engaging tone
4. Keep under {max_words} words
5. Include proper greeting and closing
6. Do not include placeholder brackets or template markers
7. Make it personal and authentic
8. Use specific examples from the resume when relevant

Generate the complete cover letter now:"""

            return self.claude.prompt(prompt, timeout=90)

        finally:
            db.close()

    def calculate_job_match(
        self,
        job_id: int,
        user_profile_id: int,
    ) -> Dict:
        """
        Calculate AI-powered job match score.

        Args:
            job_id: Job database ID
            user_profile_id: User profile ID

        Returns:
            Dictionary with match_score, matching_skills, missing_skills, recommendation
        """
        db = SessionLocal()

        try:
            # Get job and profile
            job = db.query(Job).filter(Job.id == job_id).first()
            profile = db.query(UserProfile).filter(UserProfile.id == user_profile_id).first()

            if not job or not profile:
                raise ValueError("Job or profile not found")

            # Get user's skills
            from backend.app.models import Skill

            skills = db.query(Skill).filter(Skill.user_id == user_profile_id).all()
            skill_list = [f"{s.name} ({s.proficiency or 'N/A'})" for s in skills]

            # Build prompt
            prompt = f"""Analyze how well this candidate matches the job requirements.

Job:
- Company: {job.company}
- Title: {job.title}
- Description: {job.description or 'Not provided'}
- Requirements: {job.requirements or 'See description'}

Candidate Skills:
{chr(10).join('- ' + s for s in skill_list) if skill_list else 'None listed'}

Analyze and provide JSON output with:
{{
  "match_score": <0-100 integer>,
  "matching_skills": [<list of skills that match>],
  "missing_skills": [<list of important missing skills>],
  "recommendation": "<apply/maybe/skip>",
  "reasoning": "<brief explanation>"
}}

Provide ONLY the JSON object, no other text:"""

            result = self.claude.prompt_json(prompt, timeout=60)

            # Ensure match_score is float 0-1
            if "match_score" in result:
                result["match_score"] = float(result["match_score"]) / 100

            return result

        finally:
            db.close()

    def suggest_answer(
        self,
        question_text: str,
        job_id: Optional[int] = None,
        user_profile_id: Optional[int] = None,
        field_type: str = "text",
    ) -> str:
        """
        Suggest answer to a question using AI.

        Args:
            question_text: Question to answer
            job_id: Optional job context
            user_profile_id: Optional user profile
            field_type: Field type

        Returns:
            Suggested answer
        """
        db = SessionLocal()

        try:
            context_parts = [f"Question: {question_text}"]

            # Add job context if available
            if job_id:
                job = db.query(Job).filter(Job.id == job_id).first()
                if job:
                    context_parts.append(f"\nJob Context:")
                    context_parts.append(f"- Company: {job.company}")
                    context_parts.append(f"- Title: {job.title}")
                    context_parts.append(f"- Description: {(job.description or '')[:200]}...")

            # Add profile context if available
            if user_profile_id:
                profile = db.query(UserProfile).filter(UserProfile.id == user_profile_id).first()
                if profile:
                    context_parts.append(f"\nCandidate Profile:")
                    context_parts.append(f"- Name: {profile.name}")
                    context_parts.append(f"- Work Authorization: {profile.work_authorization or 'Not specified'}")

            # Build prompt based on field type
            if field_type == "yes_no":
                context_parts.append("\nProvide answer as 'yes' or 'no' only:")
            elif field_type == "number":
                context_parts.append("\nProvide answer as a number only:")
            else:
                context_parts.append("\nProvide a concise, professional answer (2-3 sentences max):")

            prompt = "\n".join(context_parts)

            return self.claude.prompt(prompt, timeout=45)

        finally:
            db.close()

    def batch_suggest_answers(
        self,
        questions: list,
        job_id: Optional[int] = None,
        user_profile_id: Optional[int] = None,
    ) -> Dict[int, str]:
        """
        Suggest answers for multiple questions at once.

        Args:
            questions: List of (question_id, question_text, field_type) tuples
            job_id: Optional job context
            user_profile_id: Optional user profile

        Returns:
            Dictionary mapping question_id to suggested answer
        """
        suggestions = {}

        for question_id, question_text, field_type in questions:
            try:
                answer = self.suggest_answer(
                    question_text=question_text,
                    job_id=job_id,
                    user_profile_id=user_profile_id,
                    field_type=field_type,
                )
                suggestions[question_id] = answer
            except Exception as e:
                print(f"Error suggesting answer for question {question_id}: {e}")
                suggestions[question_id] = None

        return suggestions

    def analyze_resume_for_job(
        self,
        job_id: int,
        user_profile_id: int,
    ) -> Dict:
        """
        Analyze which resume version to use and suggest improvements.

        Args:
            job_id: Job database ID
            user_profile_id: User profile ID

        Returns:
            Analysis with recommended resume and suggestions
        """
        db = SessionLocal()

        try:
            # Get job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                raise ValueError("Job not found")

            # Get resumes
            from backend.app.models import Resume

            resumes = db.query(Resume).filter(Resume.user_id == user_profile_id).all()

            if not resumes:
                return {"recommended_resume_id": None, "suggestions": ["No resumes found"]}

            # Build prompt
            resume_info = "\n".join([
                f"Resume {r.id}: {r.title or r.file_name} (tags: {r.tags or 'none'})"
                for r in resumes
            ])

            prompt = f"""Analyze which resume is best for this job.

Job:
- Title: {job.title}
- Company: {job.company}
- Description: {(job.description or '')[:300]}...

Available Resumes:
{resume_info}

Provide JSON:
{{
  "recommended_resume_id": <resume_id>,
  "reasoning": "<why this resume>",
  "suggestions": ["<improvement 1>", "<improvement 2>"]
}}

JSON only:"""

            return self.claude.prompt_json(prompt, timeout=45)

        finally:
            db.close()
