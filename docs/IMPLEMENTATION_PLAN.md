# Implementation Plan

This document breaks the next DocGen milestone into executable engineering tasks.

## 1. Milestone Goal

Deliver the first meaningful product-fit upgrade for DocGen by improving:

1. requirement clarification
2. outline control
3. partial rewrite
4. feedback write-back

These changes should make the first draft more relevant and reduce the amount of manual editing users need to do outside the tool.

## 2. Delivery Principles

- Keep the current end-to-end generation flow working
- Add new state and storage carefully to avoid breaking recovery
- Ship vertical slices with tests, not large unfinished scaffolding
- Prefer project-scoped persisted data over transient prompt-only behavior

## 3. Workstreams

### Workstream A: Requirement Clarification

#### Goal

Make outline generation depend on a structured design brief instead of topic alone.

#### User Experience

Before outline generation, the user should be asked a short interview-like sequence:

- what is this document for
- who is it for
- how deep should it go
- whether it should include roadmap / interview highlights / examples
- whether it should focus more on concepts or practice

Then DocGen should generate a concise design brief and ask for confirmation before generating the full outline.

#### Engineering Tasks

1. Add a design-brief model
2. Persist the design brief per project
3. Add clarification prompts in interactive flow
4. Inject the design brief into outline generation
5. Add confirmation loop before final outline generation

#### Suggested Files

- `src/doc_gen/models/project.py`
- `src/doc_gen/cli/prompts.py`
- `src/doc_gen/cli/commands.py`
- `run.py`
- `src/doc_gen/core/outline.py`
- `src/doc_gen/storage/project.py`

#### Suggested Data Additions

- `design_brief.json`
- `learning_mode`
- `selected_modules`
- `goal_type`

#### Test Coverage

- model creation and serialization
- storage save/load for design brief
- prompt flow behavior
- outline generation uses design brief fields
- status flow remains valid

### Workstream B: Outline Control

#### Goal

Reduce oversized or unfocused outlines and make structure generation more intentional.

#### User Experience

Users should be able to control:

- compact / standard / in-depth mode
- max chapter count
- whether roadmap, interview, glossary, or recap sections appear
- whether the content is concept-heavy or practice-heavy

#### Engineering Tasks

1. Add outline constraints model
2. Extend project configuration to store selected modules and constraints
3. Update outline prompt template to respect constraints
4. Add prompt logic that requests shorter or more focused structures
5. Add validation around chapter count and mode defaults

#### Suggested Files

- `src/doc_gen/models/project.py`
- `src/doc_gen/cli/prompts.py`
- `src/doc_gen/core/outline.py`
- `src/doc_gen/llm/prompts/outline.txt`
- `src/doc_gen/storage/project.py`

#### Test Coverage

- constraints defaulting behavior
- serialization and reload
- outline prompt composition includes selected constraints
- edge cases for compact vs in-depth modes

### Workstream C: Partial Rewrite

#### Goal

Allow users to improve only the chapter or section that needs work.

#### User Experience

Examples:

- rewrite chapter 3 to be more beginner-friendly
- expand section 2.2 with more examples
- simplify the glossary-heavy section

#### Engineering Tasks

1. Add rewrite request model
2. Add section/chapter selection logic
3. Build a rewrite pipeline using existing chapter context
4. Save revised content back to the correct chapter file
5. Track revision history
6. Add CLI command for rewrite

#### Suggested Files

- `src/doc_gen/models/document.py`
- `src/doc_gen/models/project.py`
- `src/doc_gen/core/content.py`
- `src/doc_gen/core/generator.py`
- `src/doc_gen/cli/main.py`
- `src/doc_gen/cli/commands.py`
- `src/doc_gen/storage/project.py`

#### Suggested New Command

```bash
doc-gen rewrite <project> --chapter 3
doc-gen rewrite <project> --chapter 2 --section "2.2"
doc-gen rewrite <project> --chapter 4 --goal "add more examples"
```

#### Test Coverage

- chapter targeting
- section targeting
- rewrite intent propagation
- rewrite persistence
- original content is not lost without versioning

### Workstream D: Feedback Write-Back

#### Goal

Turn user feedback into persistent editorial rules that influence later rewrites and future generation.

#### User Experience

Examples:

- use more practical examples throughout the rest of the document
- keep terminology beginner-friendly
- rename "function calling" to "tool calling"

#### Engineering Tasks

1. Add editorial feedback model
2. Store project-level editorial rules
3. Add CLI path for submitting feedback
4. Feed editorial rules into rewrite and future chapter generation
5. Track feedback source and timestamps

#### Suggested Files

- `src/doc_gen/models/project.py`
- `src/doc_gen/core/generator.py`
- `src/doc_gen/core/content.py`
- `src/doc_gen/cli/main.py`
- `src/doc_gen/cli/commands.py`
- `src/doc_gen/storage/project.py`

#### Suggested Persistence

- `editor_feedback.json`
- `revisions/`

#### Test Coverage

- feedback persistence
- feedback merge rules
- future generation receives prior editorial guidance
- rewrite flow includes stored rules

## 4. Recommended Delivery Order

### Slice 1: Design Brief Foundation

Ship:

- new models
- storage support
- interactive clarification prompts
- design brief confirmation

Why first:

- outline quality depends on this
- later modules can reuse the same structured project context

### Slice 2: Outline Constraints

Ship:

- learning mode
- selected modules
- max chapter count
- outline prompt updates

Why second:

- directly addresses the biggest current product pain: oversized outlines

### Slice 3: Rewrite Command

Ship:

- rewrite data model
- chapter-level rewrite
- revision persistence

Why third:

- provides immediate editing-loop value without waiting for section-level precision

### Slice 4: Feedback Persistence

Ship:

- project-level editorial rules
- reuse in rewrite flow
- reuse in future generation flow

Why fourth:

- builds on rewrite infrastructure and makes revisions cumulative

### Slice 5: Section-Level Rewrite

Ship:

- section index
- section selection
- smaller rewrite scope

Why fifth:

- more precise but depends on the earlier rewrite foundation

## 5. Proposed File-Level Backlog

### Models

- Extend `src/doc_gen/models/project.py`
- Possibly add dedicated models in `src/doc_gen/models/document.py` or a new `revision.py`

New model candidates:

- `DesignBrief`
- `OutlineConstraints`
- `LearningModule`
- `RewriteRequest`
- `EditorialRule`
- `RevisionRecord`

### Storage

- Extend `src/doc_gen/storage/project.py`

New persistence helpers:

- `save_design_brief()`
- `load_design_brief()`
- `save_editor_feedback()`
- `load_editor_feedback()`
- `append_revision_record()`
- `list_revision_records()`

### CLI

- Extend `src/doc_gen/cli/prompts.py`
- Extend `src/doc_gen/cli/commands.py`
- Extend `src/doc_gen/cli/main.py`
- Extend `run.py`

New CLI surfaces:

- clarification prompts
- rewrite command
- feedback command

### Core

- Extend `src/doc_gen/core/outline.py`
- Extend `src/doc_gen/core/content.py`
- Extend `src/doc_gen/core/generator.py`

New core responsibilities:

- design brief aware outline generation
- constraint-aware outline generation
- rewrite orchestration
- editorial-rule injection into prompts

## 6. Testing Plan

Add or extend tests in:

- `tests/test_models.py`
- `tests/test_storage.py`
- `tests/test_content_generator.py`
- `tests/test_review_feedback_integration.py`
- a new `tests/test_outline_constraints.py`
- a new `tests/test_rewrite_flow.py`

Recommended order:

1. tests for models and storage
2. tests for prompt/context construction
3. tests for CLI command behavior
4. tests for rewrite persistence and feedback inheritance

## 7. Definition of Done

This milestone is done when:

- outline generation uses a confirmed design brief
- users can constrain outline breadth and included modules
- users can rewrite at least one chapter from the CLI
- user feedback is persisted and reused in later generation
- regression tests cover the new storage and generation paths

## 8. Suggested Next Document Updates

Once implementation starts, add:

- `docs/REVISION_WORKFLOW.md`
- `docs/SOURCE_CONNECTORS.md`
- `docs/STYLE_TEMPLATES.md`

These should follow after the first implementation slice lands, not before.
