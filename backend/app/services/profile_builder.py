"""Profile builder service to auto-populate profile from resume."""
import json
from typing import Dict, List, Optional

from backend.app.database.session import SessionLocal
from backend.app.models import Education, Resume, Skill, UserProfile, WorkHistory


class ProfileBuilder:
    """Build user profile automatically from parsed resume."""

    def __init__(self):
        """Initialize profile builder."""
        self.db = SessionLocal()

    def build_from_resume(self, resume_id: int, user_id: int) -> Dict:
        """
        Build profile data from parsed resume.

        Args:
            resume_id: Resume ID
            user_id: User profile ID

        Returns:
            Dictionary with suggested profile data
        """
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume or not resume.parsed_content:
            raise ValueError("Resume not found or not parsed")

        parsed = json.loads(resume.parsed_content)

        suggestions = {
            "profile_updates": {},
            "skills_to_add": [],
            "work_history_to_add": [],
            "education_to_add": [],
        }

        # Extract profile information
        if parsed.get('emails'):
            suggestions["profile_updates"]["email"] = parsed['emails'][0]

        if parsed.get('phones'):
            suggestions["profile_updates"]["phone"] = parsed['phones'][0]

        # Extract URLs
        urls = parsed.get('urls', [])
        for url in urls:
            url_lower = url.lower()
            if 'linkedin.com' in url_lower:
                suggestions["profile_updates"]["linkedin_url"] = url
            elif 'github.com' in url_lower:
                suggestions["profile_updates"]["github_url"] = url
            elif any(x in url_lower for x in ['portfolio', 'website', 'personal']):
                suggestions["profile_updates"]["portfolio_url"] = url

        # Extract skills
        if parsed.get('skills'):
            # Check which skills don't exist yet
            existing_skills = self.db.query(Skill.name).filter(
                Skill.user_id == user_id
            ).all()
            existing_skill_names = {s[0].lower() for s in existing_skills}

            for skill in parsed['skills']:
                if skill.lower() not in existing_skill_names:
                    suggestions["skills_to_add"].append({
                        "name": skill.title(),
                        "category": "technical",
                        "proficiency": None,
                    })

        # Try to extract work history from experience section
        if parsed.get('sections', {}).get('experience'):
            exp_text = parsed['sections']['experience']
            work_entries = self._parse_experience_section(exp_text)
            suggestions["work_history_to_add"] = work_entries

        # Try to extract education
        if parsed.get('sections', {}).get('education'):
            edu_text = parsed['sections']['education']
            edu_entries = self._parse_education_section(edu_text)
            suggestions["education_to_add"] = edu_entries

        return suggestions

    def _parse_experience_section(self, text: str) -> List[Dict]:
        """Parse experience section to extract work history entries."""
        entries = []

        # This is a basic implementation
        # In production, you'd use NLP or Claude AI for better extraction
        lines = text.split('\n')

        current_entry = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    entries.append(current_entry)
                    current_entry = {}
                continue

            # Try to detect company/title patterns
            # Pattern: "Title at Company" or "Company - Title"
            if ' at ' in line.lower():
                parts = line.split(' at ', 1)
                if len(parts) == 2:
                    current_entry = {
                        "title": parts[0].strip(),
                        "company": parts[1].strip(),
                        "description": "",
                    }
            elif ' - ' in line and not line.startswith('-'):
                parts = line.split(' - ', 1)
                if len(parts) == 2:
                    current_entry = {
                        "company": parts[0].strip(),
                        "title": parts[1].strip(),
                        "description": "",
                    }
            elif current_entry:
                # Add to description
                if "description" in current_entry:
                    current_entry["description"] += line + "\n"

        if current_entry:
            entries.append(current_entry)

        return entries[:5]  # Limit to 5 most recent

    def _parse_education_section(self, text: str) -> List[Dict]:
        """Parse education section to extract education entries."""
        entries = []

        lines = text.split('\n')

        current_entry = {}
        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    entries.append(current_entry)
                    current_entry = {}
                continue

            # Look for degree patterns
            degree_keywords = ['bachelor', 'master', 'phd', 'b.s.', 'm.s.', 'b.a.', 'm.a.']
            if any(keyword in line.lower() for keyword in degree_keywords):
                # Try to extract degree and institution
                if ' in ' in line.lower():
                    parts = line.split(' in ', 1)
                    current_entry = {
                        "degree": parts[0].strip(),
                        "field_of_study": parts[1].strip(),
                        "institution": "",
                    }
                else:
                    current_entry = {
                        "degree": line,
                        "institution": "",
                    }
            elif current_entry and not current_entry.get("institution"):
                # Next line might be the institution
                current_entry["institution"] = line

        if current_entry:
            entries.append(current_entry)

        return entries[:3]  # Limit to 3

    def apply_suggestions(
        self,
        user_id: int,
        suggestions: Dict,
        selected_fields: Optional[List[str]] = None,
    ) -> Dict:
        """
        Apply selected suggestions to user profile.

        Args:
            user_id: User profile ID
            suggestions: Dictionary from build_from_resume
            selected_fields: List of fields to apply (None = all)

        Returns:
            Dictionary with applied counts
        """
        profile = self.db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if not profile:
            raise ValueError("Profile not found")

        counts = {
            "profile_fields_updated": 0,
            "skills_added": 0,
            "work_history_added": 0,
            "education_added": 0,
        }

        # Apply profile updates
        if selected_fields is None or "profile" in selected_fields:
            for field, value in suggestions["profile_updates"].items():
                if not getattr(profile, field, None):  # Only update if empty
                    setattr(profile, field, value)
                    counts["profile_fields_updated"] += 1

        # Add skills
        if selected_fields is None or "skills" in selected_fields:
            for skill_data in suggestions["skills_to_add"]:
                skill = Skill(
                    user_id=user_id,
                    name=skill_data["name"],
                    category=skill_data["category"],
                    proficiency=skill_data["proficiency"],
                )
                self.db.add(skill)
                counts["skills_added"] += 1

        # Add work history
        if selected_fields is None or "work_history" in selected_fields:
            for work_data in suggestions["work_history_to_add"]:
                if work_data.get("company") and work_data.get("title"):
                    work = WorkHistory(
                        user_id=user_id,
                        company=work_data["company"],
                        title=work_data["title"],
                        start_date=work_data.get("start_date", "Unknown"),
                        description=work_data.get("description", ""),
                    )
                    self.db.add(work)
                    counts["work_history_added"] += 1

        # Add education
        if selected_fields is None or "education" in selected_fields:
            for edu_data in suggestions["education_to_add"]:
                if edu_data.get("degree"):
                    edu = Education(
                        user_id=user_id,
                        institution=edu_data.get("institution", "Unknown"),
                        degree=edu_data["degree"],
                        field_of_study=edu_data.get("field_of_study"),
                    )
                    self.db.add(edu)
                    counts["education_added"] += 1

        self.db.commit()
        return counts

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
