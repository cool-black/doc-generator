# Changelog

All notable changes to the DocGen project are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased] - 2026-03-23

### Added

#### Configuration System
- Added `.env` file support for LLM API configuration
  - `LLM_PROVIDER` - Provider selection (openai/anthropic/openrouter/openai_compatible)
  - `LLM_API_KEY` - API key
  - `LLM_MODEL` - Model name (e.g., kimi-k2.5)
  - `LLM_BASE_URL` - Custom base URL for API endpoints
  - `LLM_TEMPERATURE` - Temperature setting (default: 0.7)
  - `LLM_TIMEOUT` - Request timeout (default: 120s)
- Added `config.yaml` support for app-level configuration
- Added `check_api_connection()` to validate API configuration before use

#### CLI & Interactive Workflow
- Created `run.py` - Interactive workflow runner with 5-step process:
  1. API connection check
  2. Project setup (with domain, type, audience, granularity, language selection)
  3. Outline generation with user confirmation
  4. Content generation with progress logging
  5. Automatic document export
- Added `prompt_language()` - Language selection for document generation
  - Supports: 简体中文, English, 日本語, 한국어, Français, Deutsch, Español
- Added `prompt_output_dir()` - Interactive output directory selection
  - Validates parent directory exists
  - Checks write permissions
  - Creates directory if needed

#### Core Features
- **Outline Generation**: AI-powered hierarchical document structure generation
- **Content Generation**: Sequential chapter generation with context preservation
  - Terminology glossary maintained across chapters
  - Preceding context carried forward
  - Progress logging for each chapter
- **Document Assembly**: Combines chapters into final Markdown with TOC
- **Custom Output Directory**: Users can specify custom export location

#### Data Models
- `ProjectConfig` - Project configuration with status tracking
  - Added `language` field with 7 supported languages
- `Outline` / `OutlineSection` - Document structure
- `GenerationContext` - Context passed to each chapter generation
  - Added `language` field for language-aware generation
- `ChapterResult` - Chapter generation results with tokens and duration
- `Language` - Enum for supported document languages

#### Storage & Persistence
- SQLite database for project metadata
- File system storage for:
  - Project meta.json
  - outline.md
  - chapters/*.md
  - output/final.md
- Custom output directory support via `output_dir` field

#### LLM Client
- Unified async LLM client supporting multiple providers
- OpenAI-compatible API support
- Anthropic API support
- Automatic retry with exponential backoff
- Error handling for 4xx/5xx responses
- Token usage tracking

#### Logging
- Added structured logging throughout the system
- Chapter generation progress logging
- LLM API request/response logging (debug level)
- Error details with traceback in run.py

### Fixed

#### Event Loop Issues
- Fixed "Event loop is closed" error on Windows by using `WindowsSelectorEventLoopPolicy`
- Fixed `check_api_connection()` double `asyncio.run()` issue by using persistent event loop

#### TOC & Chapter Numbering
- Fixed TOC showing wrong chapter titles
- Fixed duplicate numbering in chapter headings (e.g., "## 1. 1. 开篇导读")
- Added `_strip_number_prefix()` to clean titles from outline

#### Error Handling
- Improved error messages with exception type and full traceback
- Better 400 error handling for temperature restrictions

### Changed

#### Audience Selection
- Changed `audience` from free-form text to predefined options:
  - 无基础入门者 (beginner)
  - 有一定基础的开发者 (intermediate)
  - 有经验的专业人员 (advanced)
  - 领域专家/研究人员 (expert)

### Technical Debt

#### Known Issues
- `asyncio` import unused warning in generator.py (line 5)
- `Outline` import unused warning in generator.py (line 14)
- `output_format` parameter unused in export_document (line 128)

#### TDD Workflow
- Added TDD workflow configuration ([docs/TDD_WORKFLOW.md](docs/TDD_WORKFLOW.md))
- Added `pytest.ini` with test markers and configuration
- Added test script `scripts/test.py` for convenient test running
- Added TDD example tests (`tests/test_content_generator.py`)
- Updated [CLAUDE.md](CLAUDE.md) with TDD development guidelines

#### Testing Status
- Test infrastructure in place with pytest
- Current coverage: ~42% (target: 80%+)
- CLI tests need completion
- Integration tests pending

---

## Milestone Completion Status

### Milestone 1: Foundation ✅
- [x] Project scaffolding
- [x] Configuration system (YAML + Pydantic)
- [x] LLM client abstraction
- [x] Basic CLI structure
- [x] Local storage implementation

### Milestone 2: Outline Stage ✅
- [x] Interactive requirement collection
- [x] File upload support
- [x] Outline generation
- [x] Outline editing flow
- [x] Project state management

### Milestone 3: Content Generation ✅
- [x] Chapter generation
- [x] Sequential processing
- [x] Terminology consistency (basic)
- [x] Document assembly with TOC
- [x] Markdown output

### Milestone 4: Quality Assurance 🚧
- [ ] Sub-agent review system
- [ ] Hallucination detection prompts
- [ ] Automatic regeneration loop
- [ ] Quality metrics tracking

### Milestone 5: Source Integration 🚧
- [ ] Web crawler
- [ ] Source authority ranking
- [ ] Conflict detection
- [ ] Enhanced file parsing (pdf, docx)

### Milestone 6: Polish & Export 🚧
- [ ] Mermaid diagram generation
- [ ] Word export (DOCX)
- [ ] Partial regeneration
- [ ] Plagiarism detection

---

## Commands Reference

### Interactive Workflow
```bash
python run.py
```

### Manual CLI
```bash
# Initialize
python -m doc_gen init

# Create project
python -m doc_gen new <name>

# Generate outline
python -m doc_gen generate <name> --stage outline

# Generate content
python -m doc_gen generate <name> --stage content

# Export
python -m doc_gen export <name>

# List projects
python -m doc_gen list
```

### Development
```bash
# Install
pip install -e ".[dev]"

# Tests
pytest tests/ -v

# Type check
mypy src/doc_gen

# Lint
ruff check src/
```
