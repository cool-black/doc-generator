"""Outline data structures."""

from __future__ import annotations

from pydantic import BaseModel, Field


class OutlineSection(BaseModel):
    """A section in the document outline (supports nesting)."""

    title: str
    description: str = ""
    level: int = 1  # 1=chapter, 2=section, 3=subsection
    children: list[OutlineSection] = Field(default_factory=list)


class Outline(BaseModel):
    """Complete document outline."""

    title: str
    sections: list[OutlineSection] = Field(default_factory=list)

    def to_markdown(self) -> str:
        """Render outline as Markdown."""
        lines = [f"# {self.title}", ""]
        for section in self.sections:
            self._render_section(section, lines)
        return "\n".join(lines)

    def _render_section(self, section: OutlineSection, lines: list[str]) -> None:
        prefix = "#" * (section.level + 1)
        lines.append(f"{prefix} {section.title}")
        if section.description:
            lines.append(f"\n{section.description}\n")
        else:
            lines.append("")
        for child in section.children:
            self._render_section(child, lines)

    def chapter_titles(self) -> list[str]:
        """Return list of top-level chapter titles."""
        return [s.title for s in self.sections]
