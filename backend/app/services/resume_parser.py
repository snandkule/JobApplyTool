"""Resume parsing service to extract content from PDF/DOCX files."""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional

# PDF parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# DOCX parsing
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class ResumeParser:
    """Parse resume files and extract structured information."""

    def __init__(self):
        """Initialize resume parser."""
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    def parse_file(self, file_path: Path) -> Dict:
        """
        Parse resume file and extract content.

        Args:
            file_path: Path to resume file

        Returns:
            Dictionary with parsed content
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")

        # Determine file type and parse
        ext = file_path.suffix.lower()

        if ext == '.pdf':
            raw_text = self._parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            raw_text = self._parse_docx(file_path)
        elif ext == '.txt':
            raw_text = self._parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Extract structured information
        parsed_data = {
            "raw_text": raw_text,
            "emails": self._extract_emails(raw_text),
            "phones": self._extract_phones(raw_text),
            "urls": self._extract_urls(raw_text),
            "skills": self._extract_skills(raw_text),
            "sections": self._extract_sections(raw_text),
            "word_count": len(raw_text.split()),
            "char_count": len(raw_text),
        }

        return parsed_data

    def _parse_pdf(self, file_path: Path) -> str:
        """Parse PDF file."""
        if not PDF_AVAILABLE:
            return "PDF parsing not available. Install PyPDF2: pip install PyPDF2"

        try:
            text = []
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())

            return "\n".join(text)
        except Exception as e:
            return f"Error parsing PDF: {str(e)}"

    def _parse_docx(self, file_path: Path) -> str:
        """Parse DOCX file."""
        if not DOCX_AVAILABLE:
            return "DOCX parsing not available. Install python-docx: pip install python-docx"

        try:
            doc = DocxDocument(file_path)
            text = []
            for paragraph in doc.paragraphs:
                text.append(paragraph.text)

            return "\n".join(text)
        except Exception as e:
            return f"Error parsing DOCX: {str(e)}"

    def _parse_txt(self, file_path: Path) -> str:
        """Parse TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error parsing TXT: {str(e)}"

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses."""
        emails = self.email_pattern.findall(text)
        return list(set(emails))  # Remove duplicates

    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers."""
        phones = self.phone_pattern.findall(text)
        return list(set(phones))

    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs."""
        urls = self.url_pattern.findall(text)
        return list(set(urls))

    def _extract_skills(self, text: str) -> List[str]:
        """
        Extract potential skills from text.

        This is a basic implementation that looks for common technical skills.
        Can be enhanced with ML models for better accuracy.
        """
        # Common technical skills to look for
        common_skills = [
            # Programming languages
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'go', 'rust', 'swift', 'kotlin',
            # Web technologies
            'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'fastapi', 'spring boot',
            # Databases
            'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'dynamodb',
            # Cloud
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins',
            # Data science
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'spark',
            # Tools
            'git', 'github', 'gitlab', 'jira', 'confluence',
        ]

        text_lower = text.lower()
        found_skills = []

        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill)

        return found_skills

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract common resume sections.

        Looks for headers like:
        - Experience / Work Experience
        - Education
        - Skills
        - Projects
        - Certifications
        """
        sections = {}

        # Common section headers
        section_patterns = {
            'experience': r'(?:work\s+)?experience|employment\s+history',
            'education': r'education|academic\s+background',
            'skills': r'skills|technical\s+skills|core\s+competencies',
            'projects': r'projects|portfolio',
            'certifications': r'certifications?|licenses?',
            'summary': r'summary|objective|profile',
        }

        lines = text.split('\n')
        current_section = None
        section_content = []

        for line in lines:
            line_lower = line.lower().strip()

            # Check if this line is a section header
            matched_section = None
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line_lower):
                    # Save previous section
                    if current_section and section_content:
                        sections[current_section] = '\n'.join(section_content)

                    # Start new section
                    current_section = section_name
                    section_content = []
                    matched_section = True
                    break

            # Add line to current section if not a header
            if not matched_section and current_section:
                if line.strip():
                    section_content.append(line.strip())

        # Save last section
        if current_section and section_content:
            sections[current_section] = '\n'.join(section_content)

        return sections

    def format_for_storage(self, parsed_data: Dict) -> str:
        """
        Format parsed data as JSON for database storage.

        Args:
            parsed_data: Dictionary with parsed content

        Returns:
            JSON string
        """
        return json.dumps(parsed_data, indent=2)

    def parse_and_format(self, file_path: Path) -> str:
        """
        Parse resume and return formatted JSON string for storage.

        Args:
            file_path: Path to resume file

        Returns:
            JSON string ready for database storage
        """
        parsed_data = self.parse_file(file_path)
        return self.format_for_storage(parsed_data)


def parse_resume(file_path: Path) -> Optional[str]:
    """
    Convenience function to parse resume and return JSON string.

    Args:
        file_path: Path to resume file

    Returns:
        JSON string with parsed content, or None if parsing fails
    """
    try:
        parser = ResumeParser()
        return parser.parse_and_format(file_path)
    except Exception as e:
        print(f"Error parsing resume: {e}")
        return None
