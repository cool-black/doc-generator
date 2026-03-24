# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Principles

**Think from first principles. Start from original requirements and problem essence, not conventions or templates.**

1. **Clarify before building.** When motivation or goals are unclear, stop and discuss. Don't assume I know exactly what I want.

2. **Optimize the path.** If the goal is clear but the path isn't the shortest, tell me directly and suggest a better approach.

3. **Root cause over patches.** When problems arise, dig to the root cause. Every decision must answer "why". No band-aid fixes.

4. **Cut the noise.** Output only what matters. Remove everything that doesn't change the decision.

5. **About your answer.** Add "According to claude.md: " at every beginning of your answer. This is very important！

## Project Overview

DocGen is a CLI tool that generates comprehensive knowledge documents through conversational interaction. It transforms scattered sources (user uploads + web content) into structured, original documents with built-in quality assurance.

### Project Goal

Transform the document creation workflow from hours of manual research and writing to minutes of guided conversation, producing structured, sourced, and original documents.

### Core Workflow

1. **Requirement Gathering** - Interactive prompts for domain, document type, audience, granularity
2. **Outline Generation** - AI-generated hierarchical structure with user confirmation
3. **Content Generation** - Sequential chapter generation with context preservation
4. **Quality Assurance** - (Post-MVP) Hallucination detection, consistency checks
5. **Export** - Markdown assembly with TOC

## Architecture Overview

**Data Flow**: CLI → Core Logic → LLM Client

**Key Components**:
- **CLI Layer** (`cli/`): Command interface and interactive prompts
- **Core Logic** (`core/`): Generation orchestrator, outline/content/assembler modules
- **LLM Client** (`llm/`): Unified async client supporting multiple providers
- **Storage** (`storage/`): SQLite for metadata, filesystem for content
- **Models** (`models/`): Pydantic domain models (Project, Outline, Document)

**Key Patterns**:
- State machine: CREATED → OUTLINE_DRAFT → OUTLINE_CONFIRMED → GENERATING → COMPLETED
- Generation context passed to each LLM call (terminology + preceding context + summary)
- Storage separation: metadata in SQLite, content in flat files

## Coding Standards

### TDD Development (Test-First)

**所有功能开发必须遵循 TDD 流程：**

1. **红**: 先写测试，运行确认失败
2. **绿**: 写最小实现使测试通过
3. **重构**: 优化代码，保持测试通过

**覆盖率要求**: 80%+

```bash
# 运行测试
python -m pytest

# 带覆盖率
python -m pytest --cov=src/doc_gen --cov-fail-under=80
```

**测试文件命名**: `test_<module>.py`
**测试类命名**: `Test<Feature>`
**测试方法命名**: `test_<action>_<expected>_<context>`

详细指南: [docs/TDD_WORKFLOW.md](../docs/TDD_WORKFLOW.md)

### Project Structure
- One module per feature under `src/doc_gen/`
- Public APIs typed with Pydantic models
- Private helpers prefixed with `_`
- Tests mirror source structure under `tests/`

### Error Handling
- Specific exceptions over generic
- Log with context before raising
- User-friendly messages at CLI layer

### Async Patterns
- LLM client is async (httpx)
- Use persistent event loop on Windows to avoid ProactorEventLoop issues

## Documentation Index

| Document | Purpose |
|----------|---------|
| [product_spec.md](../product_spec.md) | Product requirements, features, milestones |
| [project_spec.md](../project_spec.md) | Technical architecture details, data models, API specs |
| [PROJECT_STATUS.md](../PROJECT_STATUS.md) | Current progress, known issues, next steps |
| [CHANGELOG.md](../CHANGELOG.md) | Feature additions and bug fixes |

## Entry Points

- **Interactive**: `python run.py` - Full workflow with prompts
- **CLI**: `python -m doc_gen <command>` - Individual commands
