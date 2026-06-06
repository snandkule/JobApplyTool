"""Knowledge base service for reusable answers with fuzzy matching."""
import json
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, List, Optional

from backend.app.database.session import SessionLocal
from backend.app.models import KnowledgeBase


class KnowledgeBaseService:
    """Manage knowledge base for question answering."""

    def __init__(self):
        """Initialize knowledge base service."""
        self.db = SessionLocal()

    def find_similar_answer(
        self,
        question_text: str,
        context: Optional[Dict] = None,
        min_confidence: float = 0.7,
    ) -> Optional[Dict]:
        """
        Find similar question in knowledge base using fuzzy matching.

        Args:
            question_text: Question to match
            context: Optional context (role, company, etc.)
            min_confidence: Minimum similarity threshold (0-1)

        Returns:
            Dictionary with answer and confidence, or None
        """
        # Normalize question
        normalized = self._normalize_text(question_text)

        # Get all knowledge base entries
        entries = self.db.query(KnowledgeBase).all()

        best_match = None
        best_confidence = 0.0

        for entry in entries:
            # Check if reuse policy allows automatic use
            if entry.reuse_policy == "always_ask":
                continue

            # Calculate similarity with normalized question
            similarity = self._calculate_similarity(normalized, entry.question_normalized)

            # Check patterns
            patterns = json.loads(entry.question_patterns) if entry.question_patterns else []
            for pattern in patterns:
                pattern_similarity = self._calculate_similarity(normalized, pattern.lower())
                similarity = max(similarity, pattern_similarity)

            # Context-dependent check
            if entry.reuse_policy == "context_dependent" and context:
                # Adjust confidence based on context match
                if not self._context_matches(entry, context):
                    similarity *= 0.5  # Reduce confidence if context doesn't match

            # Update best match
            if similarity > best_confidence and similarity >= min_confidence:
                best_confidence = similarity
                best_match = entry

        if best_match:
            # Get appropriate answer
            answer = self._get_answer_for_context(best_match, context)

            # Update usage stats
            best_match.usage_count += 1
            best_match.last_used = datetime.utcnow()
            self.db.commit()

            return {
                "answer": answer,
                "confidence": best_confidence,
                "entry_id": best_match.id,
                "reuse_policy": best_match.reuse_policy,
            }

        return None

    def add_answer(
        self,
        question_text: str,
        answer: str,
        reuse_policy: str = "always_same",
        context: Optional[Dict] = None,
    ) -> KnowledgeBase:
        """
        Add new answer to knowledge base.

        Args:
            question_text: Question text
            answer: User's answer
            reuse_policy: How to reuse (always_same, context_dependent, always_ask)
            context: Optional context information

        Returns:
            Created KnowledgeBase entry
        """
        # Normalize question
        normalized = self._normalize_text(question_text)

        # Check if similar entry exists
        existing = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.question_normalized == normalized)
            .first()
        )

        if existing:
            # Update existing entry
            if reuse_policy == "context_dependent" and context:
                # Update answer template with context-specific answer
                template = self._update_answer_template(existing, answer, context)
                existing.answer_template = template
            else:
                existing.answer = answer

            existing.reuse_policy = reuse_policy
            existing.usage_count += 1
            self.db.commit()
            return existing

        # Extract patterns
        patterns = self._extract_patterns(question_text)

        # Determine context factors
        context_factors = None
        if reuse_policy == "context_dependent" and context:
            context_factors = json.dumps(list(context.keys()))

        # Create new entry
        entry = KnowledgeBase(
            question_normalized=normalized,
            question_patterns=json.dumps(patterns),
            answer=answer if reuse_policy == "always_same" else None,
            answer_template=self._create_answer_template(answer, context) if reuse_policy == "context_dependent" else None,
            reuse_policy=reuse_policy,
            context_factors=context_factors,
            confidence=1.0,
            usage_count=0,
        )

        self.db.add(entry)
        self.db.commit()

        return entry

    def update_entry(
        self,
        entry_id: int,
        answer: Optional[str] = None,
        reuse_policy: Optional[str] = None,
        confidence: Optional[float] = None,
    ):
        """Update knowledge base entry."""
        entry = self.db.query(KnowledgeBase).filter(KnowledgeBase.id == entry_id).first()

        if not entry:
            raise ValueError(f"Entry {entry_id} not found")

        if answer is not None:
            entry.answer = answer

        if reuse_policy is not None:
            entry.reuse_policy = reuse_policy

        if confidence is not None:
            entry.confidence = confidence

        self.db.commit()

    def get_all_entries(self) -> List[KnowledgeBase]:
        """Get all knowledge base entries."""
        return self.db.query(KnowledgeBase).order_by(KnowledgeBase.usage_count.desc()).all()

    def export_knowledge_base(self) -> Dict:
        """Export knowledge base as JSON."""
        entries = self.get_all_entries()

        return {
            "exported_at": datetime.utcnow().isoformat(),
            "count": len(entries),
            "entries": [
                {
                    "question": entry.question_normalized,
                    "patterns": json.loads(entry.question_patterns) if entry.question_patterns else [],
                    "answer": entry.answer,
                    "answer_template": entry.answer_template,
                    "reuse_policy": entry.reuse_policy,
                    "confidence": entry.confidence,
                    "usage_count": entry.usage_count,
                }
                for entry in entries
            ],
        }

    def import_knowledge_base(self, data: Dict):
        """Import knowledge base from JSON."""
        for entry_data in data.get("entries", []):
            # Check if exists
            existing = (
                self.db.query(KnowledgeBase)
                .filter(KnowledgeBase.question_normalized == entry_data["question"])
                .first()
            )

            if existing:
                # Update existing
                existing.answer = entry_data.get("answer")
                existing.answer_template = entry_data.get("answer_template")
                existing.reuse_policy = entry_data.get("reuse_policy", "always_same")
                existing.confidence = entry_data.get("confidence", 1.0)
            else:
                # Create new
                entry = KnowledgeBase(
                    question_normalized=entry_data["question"],
                    question_patterns=json.dumps(entry_data.get("patterns", [])),
                    answer=entry_data.get("answer"),
                    answer_template=entry_data.get("answer_template"),
                    reuse_policy=entry_data.get("reuse_policy", "always_same"),
                    confidence=entry_data.get("confidence", 1.0),
                    usage_count=entry_data.get("usage_count", 0),
                )
                self.db.add(entry)

        self.db.commit()

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Lowercase
        text = text.lower()

        # Remove extra whitespace
        text = " ".join(text.split())

        # Remove punctuation except question mark
        text = re.sub(r'[^\w\s?]', '', text)

        return text.strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0-1)."""
        return SequenceMatcher(None, text1, text2).ratio()

    def _extract_patterns(self, question: str) -> List[str]:
        """Extract alternative patterns from question."""
        normalized = self._normalize_text(question)
        patterns = [normalized]

        # Add variations
        variations = {
            "willing to relocate": ["open to relocation", "can you move", "relocate"],
            "salary": ["compensation", "salary range", "desired salary", "salary expectations"],
            "start date": ["available to start", "availability", "when can you start"],
            "sponsorship": ["visa sponsorship", "work authorization", "require sponsorship"],
            "years of experience": ["years experience", "experience with", "how long have you"],
        }

        for key, variants in variations.items():
            if key in normalized:
                patterns.extend(variants)

        return patterns

    def _context_matches(self, entry: KnowledgeBase, context: Dict) -> bool:
        """Check if context matches entry's context factors."""
        if not entry.context_factors:
            return True

        factors = json.loads(entry.context_factors)

        # Check if all required context factors are present
        return all(factor in context for factor in factors)

    def _get_answer_for_context(self, entry: KnowledgeBase, context: Optional[Dict]) -> str:
        """Get appropriate answer based on context."""
        if entry.reuse_policy == "always_same":
            return entry.answer

        if entry.reuse_policy == "context_dependent" and entry.answer_template and context:
            # Try to extract answer from template based on context
            # For now, return the base answer
            return entry.answer or entry.answer_template

        return entry.answer or ""

    def _create_answer_template(self, answer: str, context: Optional[Dict]) -> str:
        """Create answer template with context placeholders."""
        if not context:
            return answer

        # Simple template for now
        template = {
            "base_answer": answer,
            "context": context,
        }

        return json.dumps(template)

    def _update_answer_template(
        self, entry: KnowledgeBase, answer: str, context: Dict
    ) -> str:
        """Update answer template with new context-specific answer."""
        try:
            template = json.loads(entry.answer_template) if entry.answer_template else {}
        except:
            template = {}

        # Add new context-specific answer
        context_key = json.dumps(context, sort_keys=True)
        template[context_key] = answer

        return json.dumps(template)

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
