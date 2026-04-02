# DocGen

DocGen is a CLI tool for generating structured technical tutorials, learning guides, and manuals through an AI-assisted workflow.

It is designed for developers, technical writers, and educators who want more than a one-shot text generator. DocGen helps turn a topic and supporting materials into a complete document through guided setup, outline confirmation, chapter-by-chapter generation, and final export.

## Positioning

DocGen is not trying to be a generic "write anything" assistant.

It is being shaped into a focused tool for:

- technical tutorials
- learning guides
- technical manuals

The product direction is to become an AI tutorial generation workflow that can:

- clarify user intent before outlining
- generate controlled, learning-friendly outlines
- write long-form content with context continuity
- support iterative revision and feedback incorporation
- produce richer tutorial-style output over time

## Current Capabilities

- Interactive project setup through `python run.py`
- Command-based workflow through `doc-gen`
- Outline generation with user confirmation
- Sequential chapter generation with context carry-over
- Markdown export with table of contents
- Local project storage with resume support
- Multi-provider LLM support
- Multi-language generation
- Basic automated content review and regeneration

## Planned Product Direction

The next stage focuses on four themes:

1. Requirement clarification before outline generation
2. Better outline control to avoid overly long or unfocused structures
3. Partial rewrite and feedback write-back
4. Richer tutorial content modules and source integration

For the full strategy, see [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md).

## Quick Start

### Prerequisites

- Python 3.9+
- An LLM API key

### Installation

```bash
git clone <repository>
cd doc-generator
pip install -e ".[dev]"
```

### Configuration

Create and edit `.env` with your provider settings:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your-api-key-here
LLM_MODEL=kimi-k2.5
LLM_BASE_URL=https://api.moonshot.cn/v1
```

Supported providers:

- `openai`
- `anthropic`
- `openrouter`
- `openai_compatible`

### Recommended Workflow

```bash
python run.py
```

The interactive runner walks through:

1. API connection check
2. Project setup
3. Output directory selection
4. Outline generation and confirmation
5. Content generation
6. Export

### Manual CLI Workflow

```bash
python -m doc_gen new my-tutorial
python -m doc_gen generate my-tutorial --stage outline
python -m doc_gen generate my-tutorial --stage content
python -m doc_gen export my-tutorial
python -m doc_gen list
```

## Output

Generated documents currently export to Markdown and typically include:

- YAML frontmatter
- table of contents
- structured chapters
- terminology consistency across chapters

Default output location:

```text
~/.doc-gen/data/output/{project_name}.md
```

## Development

```bash
pytest -q
mypy src/doc_gen
ruff check src
```

Current verified test result:

- `109 passed, 1 skipped`

## Documentation

Start here:

- [docs/DOCUMENTATION_MAP.md](docs/DOCUMENTATION_MAP.md) - full documentation map

Core project documents:

- [product_spec.md](product_spec.md) - product requirements and roadmap
- [project_spec.md](project_spec.md) - technical architecture and extension design
- [PROJECT_STATUS.md](PROJECT_STATUS.md) - current implementation status
- [CHANGELOG.md](CHANGELOG.md) - change history

Supporting documents:

- [docs/PRODUCT_STRATEGY.md](docs/PRODUCT_STRATEGY.md) - strategy and product direction
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - next milestone engineering plan
- [specs/README.md](specs/README.md) - change-level spec workflow
- [docs/TDD_WORKFLOW.md](docs/TDD_WORKFLOW.md) - testing workflow
- [docs/ERROR_LOG.md](docs/ERROR_LOG.md) - important implementation mistakes to avoid

## License

MIT
