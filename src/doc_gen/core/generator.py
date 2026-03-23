"""Main generation orchestrator."""

from __future__ import annotations

import asyncio
from pathlib import Path

from doc_gen.config.models import AppConfig
from doc_gen.core.assembler import assemble_document
from doc_gen.core.content import generate_chapter
from doc_gen.core.outline import generate_outline, parse_outline_markdown
from doc_gen.llm.client import LLMClient
from doc_gen.models.document import GenerationContext
from doc_gen.models.outline import Outline
from doc_gen.models.project import ProjectConfig, ProjectStatus
from doc_gen.sources.parser import parse_file
from doc_gen.storage.project import ProjectStorage
from doc_gen.storage.repository import ProjectRepository
from doc_gen.utils.logger import get_logger
from doc_gen.utils.text import slugify, truncate

logger = get_logger("generator")


class DocumentGenerator:
    """Orchestrates the document generation pipeline."""

    def __init__(
        self,
        app_config: AppConfig,
        repo: ProjectRepository,
        storage: ProjectStorage,
    ) -> None:
        self.app_config = app_config
        self.repo = repo
        self.storage = storage
        self.llm = LLMClient(app_config.llm)

    async def generate_outline(self, project: ProjectConfig) -> str:
        """Generate and save outline for a project."""
        # Load source materials
        source_texts = self._load_sources(project)

        # Generate outline
        outline_md, response = await generate_outline(project, self.llm, source_texts)

        # Save outline
        self.storage.save_outline(project.id, outline_md)

        # Update project status
        project.status = ProjectStatus.OUTLINE_DRAFT
        self.repo.update(project)

        # Log generation
        self.repo.log_generation(
            project.id, -1, response.prompt_tokens, response.completion_tokens, 0
        )

        return outline_md

    async def generate_content(self, project: ProjectConfig) -> list[str]:
        """Generate all chapters based on confirmed outline."""
        outline_md = self.storage.load_outline(project.id)
        if not outline_md:
            raise RuntimeError("No outline found. Generate outline first.")

        outline = parse_outline_markdown(outline_md)
        source_texts = self._load_sources(project)

        # Update status
        project.status = ProjectStatus.GENERATING
        self.repo.update(project)

        # Build terminology from project config
        glossary: dict[str, str] = {
            term: defn.definition
            for term, defn in project.terminology.items()
        }

        chapter_files: list[str] = []
        preceding_summary = ""

        for i, section in enumerate(outline.sections):
            # Build sub-outline for this chapter
            chapter_outline = self._section_to_outline_text(section)

            ctx = GenerationContext(
                project_id=project.id,
                chapter_index=i,
                chapter_title=section.title,
                chapter_outline=chapter_outline,
                outline_summary=outline_md[:500],
                preceding_context=preceding_summary,
                terminology_glossary=glossary,
                source_materials=source_texts,
                style_tone=project.style_guide.tone,
                style_person=project.style_guide.person,
                audience=project.audience,
                doc_type=project.doc_type.value.replace("_", " ").title(),
                language=project.language.value,
            )

            result = await generate_chapter(ctx, self.llm)

            # Save chapter
            slug = slugify(section.title)
            path = self.storage.save_chapter(project.id, i + 1, slug, result.content)
            chapter_files.append(str(path))

            # Update context for next chapter
            preceding_summary = truncate(result.summary, 500)

            # Update glossary with any new terms
            glossary.update(result.new_terms)

            # Log
            self.repo.log_generation(
                project.id, i, result.prompt_tokens, result.completion_tokens, result.duration_ms
            )

            logger.info("Chapter %d/%d complete", i + 1, len(outline.sections))

        # Update status
        project.status = ProjectStatus.COMPLETED
        self.repo.update(project)

        return chapter_files

    def export_document(self, project: ProjectConfig, output_format: str = "md") -> Path:
        """Assemble and export the final document."""
        chapters = self.storage.load_chapters(project.id)
        if not chapters:
            raise RuntimeError("No chapters found. Generate content first.")

        outline_md = self.storage.load_outline(project.id)
        outline = parse_outline_markdown(outline_md) if outline_md else None
        title = outline.title if outline else project.name

        # Map chapter files to (title, content)
        # Use outline section titles if available, otherwise extract from filename
        chapter_data: list[tuple[str, str]] = []
        for i, (filename, content) in enumerate(chapters):
            if outline and i < len(outline.sections):
                ch_title = outline.sections[i].title
            else:
                # Fallback: extract title from filename: "01_introduction.md" -> "Introduction"
                name_part = filename.rsplit(".", 1)[0]  # remove .md
                name_part = name_part.split("_", 1)[1] if "_" in name_part else name_part
                ch_title = name_part.replace("_", " ").title()
            chapter_data.append((ch_title, content))

        metadata = {
            "title": title,
            "domain": project.domain,
            "doc_type": project.doc_type.value,
            "audience": project.audience,
        }

        final_md = assemble_document(title, chapter_data, metadata)

        # Determine output path: use custom output_dir if set, otherwise default
        if project.output_dir:
            output_dir = Path(project.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{project.name}.md"
            output_path.write_text(final_md, encoding="utf-8")
        else:
            output_path = self.storage.save_output(project.id, "final.md", final_md)

        logger.info("Document exported to %s", output_path)
        return output_path

    def _load_sources(self, project: ProjectConfig) -> list[str]:
        """Load and parse all source files for a project."""
        texts: list[str] = []
        uploaded = self.storage.get_uploaded_files(project.id)
        for file_path in uploaded:
            try:
                text = parse_file(file_path)
                texts.append(text)
            except (ValueError, OSError) as e:
                logger.warning("Failed to parse %s: %s", file_path, e)
        return texts

    def _section_to_outline_text(self, section: any) -> str:  # type: ignore[valid-type]
        """Convert an OutlineSection to indented text."""
        lines = [section.title]
        for child in section.children:
            lines.append(f"  - {child.title}")
            for sub in child.children:
                lines.append(f"    - {sub.title}")
        return "\n".join(lines)

    async def close(self) -> None:
        await self.llm.close()
