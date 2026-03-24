"""Review and quality assurance models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IssueSeverity(str, Enum):
    """Severity levels for review issues."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueCategory(str, Enum):
    """Categories of review issues."""

    FACTUAL = "factual"
    CONSISTENCY = "consistency"
    TERMINOLOGY = "terminology"
    HALLUCINATION = "hallucination"


@dataclass
class ReviewIssue:
    """A single issue identified during review."""

    severity: IssueSeverity
    category: IssueCategory
    description: str
    suggestion: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "description": self.description,
            "suggestion": self.suggestion,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewIssue:
        """Create from dictionary."""
        return cls(
            severity=IssueSeverity(data["severity"]),
            category=IssueCategory(data["category"]),
            description=data["description"],
            suggestion=data["suggestion"],
        )


@dataclass
class ReviewScores:
    """Individual scores for review criteria."""

    factual_accuracy: int = 0
    consistency: int = 0
    terminology: int = 0
    hallucination_free: int = 0

    @property
    def average(self) -> float:
        """Calculate average score."""
        return sum([
            self.factual_accuracy,
            self.consistency,
            self.terminology,
            self.hallucination_free,
        ]) / 4

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return {
            "factual_accuracy": self.factual_accuracy,
            "consistency": self.consistency,
            "terminology": self.terminology,
            "hallucination_free": self.hallucination_free,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> ReviewScores:
        """Create from dictionary."""
        return cls(
            factual_accuracy=data.get("factual_accuracy", 0),
            consistency=data.get("consistency", 0),
            terminology=data.get("terminology", 0),
            hallucination_free=data.get("hallucination_free", 0),
        )


@dataclass
class ReviewResult:
    """Result of a content review."""

    overall_score: int = 0
    passed: bool = False
    scores: ReviewScores = field(default_factory=ReviewScores)
    issues: list[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    chapter_index: int = -1
    chapter_title: str = ""

    @property
    def has_hallucination(self) -> bool:
        """Check if review identified any hallucination issues."""
        return any(
            issue.category == IssueCategory.HALLUCINATION
            for issue in self.issues
        )

    @property
    def high_severity_issues(self) -> list[ReviewIssue]:
        """Get all high severity issues."""
        return [
            issue for issue in self.issues
            if issue.severity == IssueSeverity.HIGH
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "passed": self.passed,
            "scores": self.scores.to_dict(),
            "issues": [issue.to_dict() for issue in self.issues],
            "summary": self.summary,
            "chapter_index": self.chapter_index,
            "chapter_title": self.chapter_title,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewResult:
        """Create from dictionary."""
        return cls(
            overall_score=data.get("overall_score", 0),
            passed=data.get("passed", False),
            scores=ReviewScores.from_dict(data.get("scores", {})),
            issues=[
                ReviewIssue.from_dict(issue_data)
                for issue_data in data.get("issues", [])
            ],
            summary=data.get("summary", ""),
            chapter_index=data.get("chapter_index", -1),
            chapter_title=data.get("chapter_title", ""),
        )


@dataclass
class QualityMetrics:
    """Aggregated quality metrics across chapters."""

    total_chapters: int = 0
    passed_chapters: int = 0
    failed_chapters: int = 0
    total_issues: int = 0
    hallucination_count: int = 0
    average_score: float = 0.0
    score_history: list[int] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        """Calculate pass rate percentage."""
        if self.total_chapters == 0:
            return 0.0
        return (self.passed_chapters / self.total_chapters) * 100

    @property
    def hallucination_rate(self) -> float:
        """Calculate hallucination rate percentage."""
        if self.total_chapters == 0:
            return 0.0
        return (self.hallucination_count / self.total_chapters) * 100

    def add_review(self, result: ReviewResult) -> None:
        """Add a review result to metrics."""
        self.total_chapters += 1
        if result.passed:
            self.passed_chapters += 1
        else:
            self.failed_chapters += 1

        self.total_issues += len(result.issues)
        if result.has_hallucination:
            self.hallucination_count += 1

        self.score_history.append(result.overall_score)
        self.average_score = sum(self.score_history) / len(self.score_history)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_chapters": self.total_chapters,
            "passed_chapters": self.passed_chapters,
            "failed_chapters": self.failed_chapters,
            "total_issues": self.total_issues,
            "hallucination_count": self.hallucination_count,
            "average_score": self.average_score,
            "pass_rate": self.pass_rate,
            "hallucination_rate": self.hallucination_rate,
            "score_history": self.score_history,
        }
