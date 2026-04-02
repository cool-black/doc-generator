# Project Specification - DocGen

## 1. Purpose

This document describes the technical architecture of DocGen as it exists today and the extension points needed for the next product phase.

DocGen is a local-first Python CLI application that orchestrates:

- project setup
- outline generation
- chapter generation
- review and recovery
- final export

The architecture should continue supporting that core flow while preparing for:

- requirement clarification before outline generation
- partial rewrite and feedback persistence
- source connectors
- richer output structure and style control

## 2. Technology Stack

| Area | Current Choice |
|------|----------------|
| Language | Python 3.9+ |
| CLI | Click |
| Configuration | Pydantic + YAML + `.env` |
| HTTP | httpx |
| Storage | SQLite + filesystem |
| Async | asyncio |
| Testing | pytest |

## 3. Current System Structure

```text
src/doc_gen/
├── cli/         # CLI entry points and prompt flow
├── config/      # App configuration loading and validation
├── core/        # Main generation pipeline
├── llm/         # Provider abstraction and prompt loading
├── models/      # Domain models
├── sources/     # Source parsing
├── storage/     # Repository and file persistence
└── utils/       # Logging and shared helpers
```

### 3.1 CLI Layer

Primary files:

- `src/doc_gen/cli/main.py`
- `src/doc_gen/cli/commands.py`
- `src/doc_gen/cli/prompts.py`
- `run.py`

Responsibilities:

- expose CLI commands
- manage interactive prompts
- validate user-facing workflow transitions
- invoke the generation pipeline

### 3.2 Core Generation Layer

Primary files:

- `src/doc_gen/core/generator.py`
- `src/doc_gen/core/outline.py`
- `src/doc_gen/core/content.py`
- `src/doc_gen/core/assembler.py`
- `src/doc_gen/core/reviewer.py`

Responsibilities:

- orchestrate outline and content generation
- build prompt context
- manage chapter sequencing
- trigger review and regeneration
- assemble final output

### 3.3 Storage Layer

Primary files:

- `src/doc_gen/storage/database.py`
- `src/doc_gen/storage/repository.py`
- `src/doc_gen/storage/project.py`
- `src/doc_gen/storage/version_history.py`

Responsibilities:

- store project metadata
- persist outlines, chapters, outputs, and version snapshots
- support resume and project lookup

### 3.4 LLM Layer

Primary files:

- `src/doc_gen/llm/client.py`
- `src/doc_gen/llm/providers.py`
- `src/doc_gen/llm/prompts/*.txt`

Responsibilities:

- normalize provider calls
- load prompt templates
- count tokens and manage retries

## 4. Current Workflow

### 4.1 Interactive Workflow

`run.py` currently provides the recommended end-to-end path:

1. validate environment and API
2. collect project inputs
3. create a project
4. generate and confirm outline
5. generate chapters
6. export final Markdown

### 4.2 Command Workflow

Click commands support the same flow in smaller steps:

- `init`
- `new`
- `list`
- `status`
- `generate`
- `export`
- `delete`

## 5. Current Domain Model

### 5.1 Project State

DocGen uses a persisted project-status flow:

```python
CREATED
OUTLINE_DRAFT
OUTLINE_CONFIRMED
GENERATING
REVIEWING
COMPLETED
```

### 5.2 Current Project Inputs

The current project model stores:

- name
- domain
- document type
- audience
- granularity
- language
- uploaded files
- style guide
- terminology
- output directory

## 6. Storage Model

### 6.1 Current Persistence Pattern

- SQLite stores metadata and generation logs
- Filesystem stores project content

Typical structure:

```text
~/.doc-gen/
├── config.yaml
└── data/
    ├── db.sqlite
    └── projects/
        └── {project_id}/
            ├── meta.json
            ├── outline.md
            ├── chapters/
            ├── output/
            └── versions/
```

### 6.2 Why This Split Works

- metadata queries stay simple
- generated content remains easy to inspect and edit
- project recovery and snapshots are straightforward

## 7. Architectural Gaps for the Next Phase

The current codebase supports sequential document generation well, but the next product direction introduces several new technical needs.

### 7.1 Requirement Clarification Layer

Needed because outline generation should no longer depend only on the initial topic and project fields.

Additions needed:

- interview-style prompt flow before outline generation
- a persisted `design_brief`
- summary confirmation before drafting the outline

Recommended shape:

```text
project/
├── design_brief.json
├── outline.md
└── ...
```

### 7.2 Outline Control Model

Needed to avoid bloated outlines.

Additions needed:

- chapter-count limit
- depth preference
- selected learning modules
- preferred document mode such as compact, standard, in-depth

Recommended model additions:

- `outline_constraints`
- `selected_modules`
- `learning_mode`

### 7.3 Revision and Feedback Model

Needed to support partial rewrite and persistent editorial guidance.

Additions needed:

- section targeting
- structured feedback persistence
- rewrite history
- feedback-aware future generation

Recommended storage additions:

```text
project/
├── editor_feedback.json
├── revisions/
└── section_index.json
```

Recommended model additions:

- `editorial_rules`
- `rewrite_requests`
- `section_metadata`

### 7.4 Source Connector Architecture

Needed for web sources and more controlled external ingestion.

Current `sources/` code mainly focuses on parsing local files.

Recommended expansion:

```text
src/doc_gen/sources/
├── parser.py
├── connectors/
│   ├── base.py
│   ├── webpage.py
│   ├── docs_site.py
│   └── ...
└── normalizers/
```

Responsibilities:

- fetch source content
- normalize and clean content
- attach source metadata
- provide reusable extracted chunks to generation

### 7.5 Output Structure and Style Layer

Needed for tutorial-style semantic blocks and template-aware formatting.

Recommended future additions:

- semantic block model
- style profile extracted from a template or exemplar
- richer final document assembler

Potential modules:

```text
src/doc_gen/output/
├── semantic_blocks.py
├── style_profile.py
└── formatters.py
```

## 8. Target Future Flow

```text
Project Setup
  ↓
Requirement Clarification
  ↓
Design Brief Confirmation
  ↓
Outline Generation with Constraints
  ↓
Outline Confirmation
  ↓
Chapter Generation
  ↓
Review / Rewrite / Feedback Write-Back
  ↓
Final Assembly and Export
```

## 9. Engineering Priorities

### 9.1 Near-Term

- keep current generation flow stable
- avoid regressions while introducing clarification and rewrite support
- preserve local-first project storage

### 9.2 Mid-Term

- formalize source connectors
- formalize revision metadata
- improve assembly for tutorial-style content blocks

### 9.3 Documentation Rule

This file should describe implementation structure and extension design.

It should not become:

- a changelog
- a status dashboard
- a product strategy memo

Those concerns belong in:

- `CHANGELOG.md`
- `PROJECT_STATUS.md`
- `docs/PRODUCT_STRATEGY.md`
