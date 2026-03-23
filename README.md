# DocGen - Document Generator

A CLI tool that generates comprehensive knowledge documents through conversational interaction with AI.

## Features

- **Interactive Workflow**: Guided prompts for document requirements
- **AI-Powered Outline**: Automatic structure generation with user confirmation
- **Sequential Content Generation**: Chapter-by-chapter writing with context preservation
- **Custom Output Directory**: Export to your preferred location
- **Multi-Source Support**: Upload reference files (txt, md, pdf, docx)
- **Quality Assurance**: Terminology consistency across chapters

## Quick Start

### Prerequisites

- Python 3.9+
- LLM API key (OpenAI, Anthropic, Moonshot/Kimi, etc.)

### Installation

```bash
# Clone and install
git clone <repository>
cd doc-generator
pip install -e ".[dev]"
```

### Configuration

Create `.env` file from template:

```bash
copy .env.template .env
```

Edit `.env` with your API credentials:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your-api-key-here
LLM_MODEL=kimi-k2.5
LLM_BASE_URL=https://api.moonshot.cn/v1
```

Supported providers: `openai`, `anthropic`, `openrouter`, `openai_compatible`

### Usage

#### Interactive Mode (Recommended)

```bash
python run.py
```

This runs the complete workflow:
1. API connection check
2. Project setup (domain, type, audience, granularity)
3. Custom output directory selection
4. Outline generation with confirmation
5. Content generation
6. Automatic export

#### Manual CLI

```bash
# Create project
python -m doc_gen new my-tutorial

# Generate outline
python -m doc_gen generate my-tutorial --stage outline

# Generate content
python -m doc_gen generate my-tutorial --stage content

# Export document
python -m doc_gen export my-tutorial

# List projects
python -m doc_gen list
```

## Document Types

- **Tutorial**: Step-by-step learning materials
- **Technical Manual**: Reference documentation
- **Academic Paper**: Research-style document
- **Knowledge Handbook**: Comprehensive topic coverage
- **API Documentation**: Interface documentation
- **Learning Guide**: Educational content

## Output

Generated documents include:
- YAML frontmatter (metadata)
- Table of Contents
- Structured chapters with proper headings
- Consistent terminology usage

Default output: `~/.doc-gen/data/output/{project_name}.md`

Custom output: Specified during project creation

## Project Structure

```
~/.doc-gen/
├── config.yaml              # App configuration
└── data/
    ├── db.sqlite           # Project metadata
    └── projects/
        └── {project_id}/
            ├── meta.json
            ├── outline.md
            ├── chapters/
            │   ├── 01_introduction.md
            │   └── ...
            └── output/
                └── {project_name}.md
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/doc_gen

# Linting
ruff check src/
```

## Documentation

- [product_spec.md](product_spec.md) - Product requirements
- [project_spec.md](project_spec.md) - Technical architecture
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current progress
- [CHANGELOG.md](CHANGELOG.md) - Change history

## License

MIT
