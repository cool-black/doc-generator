"""Main generation orchestrator."""

from __future__ import annotations

import asyncio
from pathlib import Path

from doc_gen.config.models import AppConfig
from doc_gen.core.assembler import assemble_document
from doc_gen.core.content import generate_chapter
from doc_gen.core.outline import generate_outline, parse_outline_markdown
from doc_gen.core.reviewer import ContentReviewer
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
        enable_review: bool = True,
    ) -> None:
        self.app_config = app_config
        self.repo = repo
        self.storage = storage
        self.llm = LLMClient(app_config.llm)
        self.enable_review = enable_review

        # Initialize reviewer if enabled
        if enable_review:
            self.reviewer = ContentReviewer(
                llm_client=self.llm,
                storage=storage,
                repo=repo,
                min_score=80,
                max_retries=2,
            )
        else:
            self.reviewer = None

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
        """Generate all chapters based on confirmed outline.

        Supports resume from checkpoint - will skip already generated chapters
        and continue from where it left off.
        """
        outline_md = self.storage.load_outline(project.id)
        if not outline_md:
            raise RuntimeError("No outline found. Generate outline first.")

        outline = parse_outline_markdown(outline_md)
        source_texts = self._load_sources(project)

        # Check for existing chapters to support resume
        last_generated = self.storage.get_last_generated_chapter(project.id)
        start_index = last_generated if last_generated >= 0 else 0

        if start_index > 0:
            logger.info(
                "Resuming generation from chapter %d (%d already completed)",
                start_index + 1,
                start_index,
            )

        # Update status
        project.status = ProjectStatus.GENERATING
        self.repo.update(project)

        # Build terminology from project config
        glossary: dict[str, str] = {
            term: defn.definition
            for term, defn in project.terminology.items()
        }

        # Load existing chapters to restore context
        chapter_files: list[str] = []
        preceding_summary = ""
        existing_chapters = self.storage.load_chapters(project.id)

        # Populate chapter_files from existing chapters
        for filename, _ in existing_chapters:
            chapter_path = self.storage.project_dir(project.id) / "chapters" / filename
            chapter_files.append(str(chapter_path))

        # Restore preceding_summary from last generated chapter
        if existing_chapters and start_index > 0:
            last_chapter_content = existing_chapters[-1][1]
            preceding_summary = self._extract_summary(last_chapter_content)

        for i, section in enumerate(outline.sections):
            # Skip already generated chapters
            if i < start_index:
                logger.debug("Skipping chapter %d (already generated)", i + 1)
                continue
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

            # Generation loop with review
            chapter_content = ""
            attempt = 0
            review_result = None

            while attempt <= (2 if self.reviewer else 0):  # Max 3 attempts (initial + 2 retries)
                if attempt > 0:
                    logger.info("Regenerating chapter %d (attempt %d)", i + 1, attempt + 1)

                # Generate chapter
                result = await generate_chapter(ctx, self.llm)
                chapter_content = result.content

                # Review if enabled
                if self.reviewer and attempt < 3:
                    review_result = await self.reviewer.review_chapter(
                        project=project,
                        chapter_index=i,
                        chapter_title=section.title,
                        chapter_content=chapter_content,
                        ctx=ctx,
                    )

                    if review_result.passed:
                        logger.info(
                            "Chapter %d passed review (score: %d)",
                            i + 1,
                            review_result.overall_score,
                        )
                        break
                    elif self.reviewer.should_regenerate(review_result, attempt):
                        logger.warning(
                            "Chapter %d failed review (score: %d), regenerating...",
                            i + 1,
                            review_result.overall_score,
                        )
                        attempt += 1
                        continue
                    else:
                        logger.warning(
                            "Chapter %d failed review (score: %d), max retries reached",
                            i + 1,
                            review_result.overall_score,
                        )
                        break
                else:
                    break

            # Save chapter
            slug = slugify(section.title)
            path = self.storage.save_chapter(project.id, i + 1, slug, chapter_content)
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

    def _extract_summary(self, content: str, max_length: int = 500) -> str:
        """Extract a summary from chapter content for context passing.

        Returns the first paragraph or up to max_length characters.
        """
        # Remove markdown headers
        lines = content.split("\n")
        non_header_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                non_header_lines.append(line)

        if not non_header_lines:
            return ""

        text = " ".join(non_header_lines)
        return truncate(text, max_length)

    def get_quality_report(self) -> dict | None:
        """Get quality metrics report from reviewer.

        Returns:
            Quality metrics dictionary or None if review is disabled
        """
        if self.reviewer:
            return self.reviewer.get_metrics_report()
        return None

    async def close(self) -> None:
        if self.reviewer:
            await self.reviewer.close()
        await self.llm.close()
