# Product Specification - DocGen

## 1. Product Definition

### 1.1 What is DocGen

DocGen is a CLI product for generating structured technical tutorials, learning guides, and technical manuals through an AI-assisted workflow.

It is designed to support the full content-production path:

1. clarify the user goal
2. design an appropriate outline
3. generate long-form content chapter by chapter
4. revise selected parts with user feedback
5. export a usable final document

### 1.2 Target Users

- Developers writing tutorials or internal technical guides
- Technical writers creating structured manuals
- Educators creating learning material
- Knowledge workers converting scattered reference material into teachable documents

### 1.3 Primary Use Cases

- Generate a beginner-friendly tutorial for a technical topic
- Generate a structured learning guide for self-study
- Generate a technical manual from user requirements and source files
- Build a first draft, then iteratively revise chapters and sections

### 1.4 Value Proposition

Before DocGen:

- users gather requirements manually
- create a structure manually
- repeatedly prompt an LLM for disconnected sections
- manually fix consistency, formatting, and flow

After DocGen:

- users go through a guided workflow
- DocGen proposes a controlled outline
- content is generated as a coherent document
- later revisions can target only the parts that need work

## 2. Product Focus

### 2.1 In-Scope Document Types

- Technical Tutorial
- Learning Guide
- Technical Manual

### 2.2 De-emphasized for Now

- Academic paper generation
- Broad "knowledge handbook" positioning
- General-purpose writing or marketing content

### 2.3 Product Principles

- Focus on learning-friendly output rather than encyclopedic coverage
- Prefer controlled scope over oversized outlines
- Treat generation as an iterative workflow, not a one-shot action
- Keep the product local-first and usable from the CLI

## 3. Core Product Problems to Solve

### 3.1 Requirement Clarification

The product must avoid generating an outline from only a topic string.

Before outlining, it should clarify:

- user goal
- audience level
- expected depth
- practical vs conceptual emphasis
- desired content modules
- expected document size

### 3.2 Outline Control

The outline should not default to maximum coverage.

It should be constrained by:

- chapter count
- depth
- learning objective
- selected modules
- document length target

### 3.3 Iterative Revision

Users need to revise specific sections instead of rerunning full generation.

The product must support:

- chapter rewrite
- section rewrite
- user feedback persistence
- feedback-aware future generation

### 3.4 Learning-Oriented Content Structure

Tutorial documents should include optional modules such as:

- learning roadmap
- key concepts
- worked examples
- common mistakes
- interview highlights
- recap / summary
- glossary
- further reading

### 3.5 Source Integration

The product should progressively support:

- local file sources
- web pages
- official documentation sites
- blogs and GitHub docs
- more complex sources later, such as public-platform articles

### 3.6 Richer Presentation

Output should evolve beyond flat text and support tutorial-style semantic blocks:

- key point
- note
- warning
- example
- interview tip
- diagram placeholder
- chapter summary

## 4. Functional Requirements

### 4.1 Current Core Workflow

#### F1: Project Setup

- Collect topic, document type, audience, granularity, language
- Optionally ingest user files
- Persist project metadata locally

#### F2: Outline Generation

- Generate a draft outline from project context
- Show it to the user
- Require confirmation before continuing

#### F3: Chapter Generation

- Generate chapters sequentially
- Preserve context across chapters
- Maintain terminology consistency

#### F4: Export

- Assemble chapters into a final Markdown document
- Generate a table of contents
- Export to a project output path

### 4.2 Next-Stage Requirements

#### F5: Requirement Clarification Workflow

- Ask multi-turn questions before outline generation
- Produce a tutorial-design summary
- Require confirmation of that summary before formal outline generation

Acceptance criteria:

- outline generation is based on more than topic alone
- summary captures user goal, audience, scope, and selected modules
- users can revise the summary before continuing

#### F6: Outline Control

- Allow chapter count and scope constraints
- Allow users to toggle optional content modules
- Offer compact, standard, and in-depth tutorial modes

Acceptance criteria:

- generated outlines are shorter and more purposeful
- optional modules are included only when selected
- depth mode affects chapter breadth and structure

#### F7: Partial Rewrite

- Rewrite one chapter or one section
- Support rewrite intents such as simplify, expand, add examples, make more beginner-friendly

Acceptance criteria:

- user can target a chapter without regenerating the full document
- rewritten content reuses project context and terminology
- rewrite history is persisted

#### F8: Feedback Write-Back

- Persist user feedback as structured editorial rules
- Apply those rules in later rewrites and future generation

Acceptance criteria:

- user feedback survives across sessions
- later chapters can inherit updated writing guidance
- terminology and style changes propagate consistently

#### F9: Learning Modules

- Support optional learning roadmap
- Support optional interview highlights
- Support optional common mistakes and recap sections

Acceptance criteria:

- users can choose modules at project setup or outline stage
- generated structure reflects selected tutorial components
- content modules improve tutorial usability without bloating the whole document

#### F10: Source Connectors

- Ingest stable web sources first
- Add connector architecture for future expansion

Acceptance criteria:

- users can add URL-based sources
- extracted content becomes part of the generation context
- future source integrations do not require redesigning the whole pipeline

#### F11: Style Templates

- Allow users to provide reference documents or formatting examples
- Learn style preferences from a template or exemplar

Acceptance criteria:

- output structure can adapt to a chosen style reference
- template preference influences headings and semantic blocks
- style guidance is project-scoped

## 5. Non-Goals for the Near Term

- Real-time collaborative editing
- Web app as the primary product surface
- CMS publishing integrations
- Broad consumer writing use cases
- Fully automatic internet-scale crawling

## 6. Success Metrics

### 6.1 Product Quality

- Outline approval rate improves after clarification step
- Average outline length decreases without reducing usefulness
- Users can revise specific sections without regenerating the entire document
- Tutorial outputs include more learning-oriented structure

### 6.2 Workflow Quality

- Users can complete first draft generation end-to-end from the CLI
- Resume support works reliably after interruption
- Feedback persists across later generation steps

### 6.3 Technical Quality

- Stable local storage for project state
- Predictable generation flow and status transitions
- Reliable tests for generation, recovery, and review paths

## 7. Roadmap

### v0.2: Focus and Outline Control

- Narrow product positioning to tutorials, learning guides, and manuals
- Add requirement clarification before outlining
- Add tutorial-design summary confirmation
- Add outline length and module controls

### v0.3: Revision Loop

- Add chapter rewrite
- Add section rewrite
- Add persistent user feedback
- Feed editorial rules into later generation

### v0.4: Learning-First Output

- Add learning roadmap module
- Add interview highlights module
- Add recap, glossary, and common mistakes modules

### v0.5: Sources and Style

- Add stable web-source ingestion
- Design connector-based source architecture
- Add style-reference or template-driven generation

## 8. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Outline still too large | High | Add explicit scope controls and summary confirmation |
| Revision workflow becomes inconsistent | High | Persist rewrite history and editorial rules |
| Source quality varies | Medium | Start with stable sources and connector boundaries |
| Tutorial output feels generic | Medium | Add semantic blocks and style-reference support |
| Product scope expands again | High | Keep positioning focused on tutorial and learning documents |
