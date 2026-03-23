# Project Specification - Document Generator

## 1. Technology Stack

### 1.1 Core Technologies
| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.10+ |
| CLI Framework | Click | ^8.1 |
| Configuration | Pydantic + PyYAML | ^2.0 |
| HTTP Client | httpx | ^0.25 |
| Database | SQLite (stdlib) | - |
| Async | asyncio (stdlib) | - |

### 1.2 Document Processing
| Purpose | Library |
|---------|---------|
| PDF Parsing | PyPDF2 |
| Word Parsing | python-docx |
| HTML Parsing | beautifulsoup4 |
| Markdown | markdown |
| Similarity | difflib (stdlib) |

### 1.3 LLM Integration
- OpenAI API (GPT-4, GPT-3.5)
- Anthropic API (Claude)
- OpenRouter (unified interface)
- Support for custom base URLs (proxies)

## 2. System Architecture

### 2.1 Module Organization

```
src/doc_gen/
├── __init__.py
├── cli/                    # CLI interface layer
│   ├── __init__.py
│   ├── main.py            # Entry point and command registration
│   ├── commands.py        # Command implementations
│   └── prompts.py         # Interactive user prompts
├── config/                 # Configuration management
│   ├── __init__.py
│   ├── models.py          # Pydantic config models
│   └── loader.py          # Config file I/O
├── core/                   # Core business logic
│   ├── __init__.py
│   ├── generator.py       # Main generation orchestrator
│   ├── outline.py         # Outline generation
│   ├── content.py         # Chapter content generation
│   └── assembler.py       # Document assembly
├── llm/                    # LLM client abstraction
│   ├── __init__.py
│   ├── client.py          # Unified LLM interface
│   ├── providers.py       # Provider-specific implementations
│   └── prompts/           # Prompt templates
│       ├── outline.txt
│       ├── chapter.txt
│       └── review.txt
├── sources/                # Content source processing
│   ├── __init__.py
│   ├── parser.py          # File parsing dispatcher
│   ├── pdf_parser.py
│   ├── docx_parser.py
│   ├── txt_parser.py
│   └── web_crawler.py     # (Post-MVP)
├── quality/                # Quality assurance
│   ├── __init__.py
│   ├── reviewer.py        # Hallucination review agent
│   ├── consistency.py     # Cross-chapter consistency
│   ├── plagiarism.py      # Similarity detection
│   └── disputes.py        # Conflict detection (Post-MVP)
├── storage/                # Data persistence
│   ├── __init__.py
│   ├── project.py         # Project data models
│   ├── repository.py      # Project CRUD operations
│   └── database.py        # SQLite operations
├── models/                 # Domain models
│   ├── __init__.py
│   ├── project.py         # Project state enums
│   ├── outline.py         # Outline data structures
│   └── document.py        # Document metadata
└── utils/                  # Utilities
    ├── __init__.py
    ├── text.py            # Text processing utilities
    ├── tokens.py          # Token counting/optimization
    └── logger.py          # Logging setup
```

### 2.2 Data Models

#### Project State Machine
```python
class ProjectStatus(Enum):
    CREATED = "created"
    OUTLINE_DRAFT = "outline_draft"
    OUTLINE_CONFIRMED = "outline_confirmed"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
```

#### Project Configuration
```python
class ProjectConfig(BaseModel):
    id: str  # UUID
    name: str
    created_at: datetime
    status: ProjectStatus

    # Requirements
    domain: str
    doc_type: DocumentType
    audience: str
    granularity: Granularity

    # Sources
    user_files: List[Path]
    web_sources: List[str]  # URLs (Post-MVP)

    # Generation settings
    style_guide: Optional[StyleGuide]
    terminology: Dict[str, TermDefinition]
```

#### Generation Context
```python
class GenerationContext(BaseModel):
    project_id: str
    chapter_index: int
    chapter_title: str
    outline_summary: str
    preceding_context: str  # Previous N paragraphs
    terminology_glossary: Dict[str, str]
    source_materials: List[str]
```

## 3. Data Flow

### 3.1 Initialization Flow
```
User: doc-gen init
    ↓
CLI: Check if config exists
    ↓
[No] → Prompt for API keys → Save to ~/.doc-gen/config.yaml
[Yes] → Show current config → Prompt for changes
    ↓
Validate configuration → Success message
```

### 3.2 Project Creation Flow
```
User: doc-gen new <name>
    ↓
CLI: Create project directory structure
    ↓
Interactive Prompts:
    - Domain/topic?
    - Document type? [select]
    - Target audience?
    - Granularity? [select]
    - Upload files? [optional]
    ↓
Save ProjectConfig → meta.json
    ↓
Display: Project created, run `doc-gen generate <name> --stage outline`
```

### 3.3 Outline Generation Flow
```
User: doc-gen generate <name> --stage outline
    ↓
Load ProjectConfig
    ↓
Parse uploaded files → Extract text content
    ↓
Build LLM prompt with:
    - Project requirements
    - Source excerpts (truncated)
    ↓
Call LLM → Generate outline
    ↓
Save outline.md
    ↓
Display outline → Prompt: Edit, Regenerate, or Confirm?
    ↓
[Confirm] → Update status to OUTLINE_CONFIRMED
```

### 3.4 Content Generation Flow
```
User: doc-gen generate <name> --stage content
    ↓
Verify status == OUTLINE_CONFIRMED
    ↓
Parse outline → List of chapters
    ↓
Initialize terminology glossary from outline
    ↓
For each chapter:
    Build GenerationContext
        ↓
    Generate chapter content (LLM call)
        ↓
    Save to chapters/{index}_{slug}.md
        ↓
    Update terminology glossary
        ↓
    Update chapter summary
    ↓
Update status to COMPLETED
    ↓
Display: Chapters generated, run `doc-gen export <name>`
```

### 3.5 Document Assembly Flow
```
User: doc-gen export <name>
    ↓
Load all chapter files
    ↓
Generate Table of Contents from headings
    ↓
Assemble final.md:
    - YAML frontmatter
    - TOC
    - Chapters in order
    - References (if any)
    ↓
Save to output/final.md
    ↓
[Post-MVP] Convert to DOCX
```

## 4. Storage Structure

### 4.1 File System Layout
```
~/.doc-gen/
├── config.yaml              # User configuration
└── data/
    └── projects/
        └── {project_id}/
            ├── meta.json           # Project configuration
            ├── outline.md          # Generated outline
            ├── outline_v2.md       # User-edited outline
            ├── sources/            # User-uploaded files
            │   └── uploaded/
            ├── cache/              # Parsed source content
            │   └── extracted.json
            ├── chapters/           # Generated chapters
            │   ├── 01_introduction.md
            │   ├── 02_concepts.md
            │   └── ...
            └── output/             # Final outputs
                └── final.md
```

### 4.2 SQLite Schema
```sql
-- Projects table
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    config_json TEXT NOT NULL  -- Serialized ProjectConfig
);

-- Terminology table (shared across projects)
CREATE TABLE terminology (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    term TEXT NOT NULL,
    definition TEXT,
    aliases TEXT,  -- JSON array
    FOREIGN KEY (project_id) REFERENCES projects(id)
);

-- Generation logs for debugging
CREATE TABLE generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id TEXT,
    chapter_index INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    duration_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

## 5. LLM Integration

### 5.1 Provider Interface
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...
```

### 5.2 Prompt Template System
- Templates stored as text files in `llm/prompts/`
- Variable substitution using `{placeholder}` syntax
- Support for partial templates (headers, footers)

### 5.3 Error Handling
- Timeout: 60s default, configurable
- Retry: Exponential backoff, max 3 retries
- Fallback: Secondary provider if primary fails
- Error messages: User-friendly, suggest actions

## 6. Quality Assurance Pipeline

### 6.1 MVP: Basic Consistency
- Terminology glossary maintained across chapters
- Chapter summaries carried forward for context
- Manual user review at outline stage

### 6.2 Post-MVP: Automated Review
```
Chapter Generation
    ↓
Hallucination Review Agent
    ↓
[Pass] → Continue
[Fail] → Regenerate with feedback (max 3x)
    ↓
Consistency Check (cross-chapter)
    ↓
Plagiarism Check (vs sources)
    ↓
Mark as complete
```

## 7. CLI Command Reference

| Command | Arguments | Description |
|---------|-----------|-------------|
| `init` | - | Initialize configuration |
| `new` | `<name>` | Create new project |
| `open` | `<name>` | Open existing project |
| `list` | - | List all projects |
| `status` | `<name>` | Show project status |
| `generate` | `<name> --stage {outline\|content\|all}` | Generate content |
| `export` | `<name> --format {md\|docx}` | Export document |
| `delete` | `<name>` | Delete project |
| `config` | `[--get \| --set <key> <value>]` | Manage configuration |

## 8. Development Setup

### 8.1 Installation
```bash
git clone <repo>
cd document-gen
pip install -e ".[dev]"
doc-gen init
```

### 8.2 Testing
```bash
pytest tests/           # Unit tests
pytest tests/e2e/      # End-to-end tests
pytest --cov=src       # Coverage report
```

### 8.3 Project Structure Convention
- One module per feature
- Public APIs typed with Pydantic models
- Private helpers prefixed with `_`
- Tests mirror source structure
