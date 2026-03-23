# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Principles

**Think from first principles. Start from original requirements and problem essence, not conventions or templates.**

1. **Clarify before building.** When motivation or goals are unclear, stop and discuss. Don't assume I know exactly what I want.

2. **Optimize the path.** If the goal is clear but the path isn't the shortest, tell me directly and suggest a better approach.

3. **Root cause over patches.** When problems arise, dig to the root cause. Every decision must answer "why". No band-aid fixes.

4. **Cut the noise.** Output only what matters. Remove everything that doesn't change the decision.

## Project Overview

DocGen is a CLI tool that generates comprehensive knowledge documents through conversational interaction. It transforms scattered sources (user uploads + web content) into structured, original documents with built-in quality assurance.

**Documentation**: See [product_spec.md](../product_spec.md) for requirements and milestones, [project_spec.md](../project_spec.md) for technical architecture.

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Initialize configuration
python -m doc_gen init

# Create new project interactively
python -m doc_gen new my-project

# Generate outline (with user confirmation)
python -m doc_gen generate my-project --stage outline

# Generate content chapters
python -m doc_gen generate my-project --stage content

# Export final document
python -m doc_gen export my-project --format md
```

## Architecture

**Data Flow**: CLI (`cli/main.py`) → Core Logic (`core/generator.py`) → LLM Client (`llm/client.py`)

**Key Patterns**:
- State machine for project lifecycle: CREATED → OUTLINE_DRAFT → OUTLINE_CONFIRMED → GENERATING → COMPLETED
- Generation context (terminology glossary + preceding context + chapter summary) passed to each LLM call
- Storage: `~/.doc-gen/data/projects/{id}/` with SQLite metadata in `db.sqlite`, content in flat files

## Common Development Commands

```bash
# Run CLI in development
python -m doc_gen --help

# Run single test file
pytest tests/test_generator.py -v

# Run with coverage
pytest --cov=src/doc_gen tests/

# Type checking
mypy src/doc_gen

# Linting
ruff check src/
```

## Configuration System

Config loaded from `~/.doc-gen/config.yaml` with env var substitution:
- `llm.provider`: Resolved via Pydantic models in `config/models.py`
- Config cached in memory during CLI execution
- Project-specific config stored in SQLite per project
