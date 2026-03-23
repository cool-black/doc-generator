# Document Generator - Project Plan

## 1. Project Overview

An intelligent document generation assistant that creates comprehensive, high-quality knowledge documents based on user-specified domains or topics. The system supports multi-turn conversations to refine requirements, integrates multiple content sources, and ensures originality while maintaining factual accuracy.

## 2. Core Features

### 2.1 Document Type & Granularity
- **Selectable document types**: Tutorial, Technical Manual, Academic Paper, Knowledge Handbook, API Documentation, Learning Guide
- **Granularity levels**: Overview, Standard, Comprehensive, Deep-dive
- Determined through multi-turn conversation with the user

### 2.2 Content Sources (Priority Order)
1. **User-uploaded documents** (highest priority)
2. **Web crawling results** (ranked by authority)

**Authority Ranking for Web Sources**:
- Tier 1: Wikipedia, Official Documentation, Academic Papers
- Tier 2: Established Technical Blogs, Official Blogs
- Tier 3: Community Forums, Other Sources

### 2.3 Quality Assurance Mechanisms

#### Hallucination Guard
- **Granularity**: Chapter-level review
- **Timing**: Real-time during generation (streaming review)
- **Action**: Auto-regenerate if hallucination detected (max 3 retries)
- **Review Criteria**:
  1. Fact verifiability: Every concrete fact must have source support
  2. Source alignment: Content must match provided references
  3. Logical consistency: No self-contradicting statements
  4. Over-inference marking: Distinguish facts from AI inferences
  5. Technical accuracy: Correct terminology and runnable code examples

#### Conflict Detection
- Generates a separate **Dispute Report** document containing:
  - Summary of contradictory points
  - Views from different sources
  - Recommended adoption with reasoning
- Report format: Standalone Markdown file

#### Plagiarism Detection
- **Tool**: Python `difflib`
- **Method**: Segment-by-segment comparison with original sources
- **Threshold**: Trigger rewrite if >60% similarity or 50+ consecutive matching words
- **Action**: Flag high-similarity segments for paraphrasing

#### Consistency Management
- **Context preservation**:
  - Preceding N paragraphs (e.g., 500 words)
  - Following N paragraphs (e.g., 500 words)
  - Current chapter summary
- **Document Metadata**:
  - Terminology glossary (standardized terms)
  - Writing style guide (tone, tense, person)
  - Cross-reference mapping

### 2.4 Originality & Copyright

**Text Rewriting Strategy**:
- Paraphrase expressive content while preserving technical facts
- Preserve exact values: technical parameters, dates, version numbers
- Preserve exact sequences: step-by-step instructions, ordered lists
- Rewrite explanations, introductions, and summaries

**Diagram Generation**:
- **Tool**: Mermaid (for flowcharts, sequence diagrams, architecture diagrams)
- All diagrams regenerated from text description (no direct copying from sources)
- Supported types: Flowchart, Sequence Diagram, Class Diagram, State Diagram, ER Diagram

**Visual Originality**:
- No direct image copying from web sources
- All visuals recreated through Mermaid or AI generation

### 2.5 Token Cost Optimization

**Hierarchical Generation Pipeline**:
```
Stage 1: Outline Generation (global view, minimal tokens)
    ↓ User confirmation
Stage 2: Metadata Extraction (terminology, style guide)
    ↓
Stage 3: Parallel Chapter Generation (context-minimized)
    ↓
Stage 4: Cross-chapter Consistency Review
    ↓
Stage 5: Dispute Report Generation
    ↓
Stage 6: Final Assembly
```

**Context Minimization Techniques**:
- Terminology Glossary: Shared across all chapters (reduces repetition)
- Chapter Summaries: Compact representation of previous chapters
- No full-text carry: Only adjacent context + metadata passed to each generation
- Parallel processing: Independent chapters generated concurrently

**Per-Chapter Context Package**:
```python
{
    "terminology_glossary": {...},
    "previous_chapter_summary": "...",
    "current_chapter_outline": "...",
    "user_references": [...],
    "style_guide": {...}
}
```

### 2.6 User Interaction

**Multi-turn Conversation Flow**:
1. Initial domain/topic input
2. Document type selection
3. Target audience specification
4. Granularity level confirmation
5. Reference file upload (optional, user marks as "template" or "reference")
6. Generation parameter review

**Post-Generation Editing**:
- Support partial regeneration by section/paragraph
- Maintain consistency after edits through metadata propagation
- Version history tracking (allow rollback)

## 3. System Architecture

### 3.1 Module Structure

```
document-gen/
├── core/                       # Core business logic
│   ├── requirement_chat.py     # Requirement clarification chat
│   ├── outline_generator.py    # Document outline generation
│   ├── content_generator.py    # Chapter content generation
│   └── hallucination_guard.py  # Hallucination detection & correction
├── sources/                    # Content source processing
│   ├── file_parser.py          # Parse user uploads (PDF, DOCX, MD, TXT)
│   ├── web_crawler.py          # Web content crawling
│   ├── source_ranker.py        # Authority-based source ranking
│   └── conflict_detector.py    # Detect contradictions across sources
├── quality/                    # Quality control
│   ├── consistency_checker.py  # Cross-chapter consistency verification
│   ├── plagiarism_checker.py   # Similarity detection using difflib
│   └── coherence_validator.py  # Post-edit coherence verification
├── output/                     # Output generation
│   ├── markdown_builder.py     # Markdown document assembly
│   ├── diagram_generator.py    # Mermaid diagram generation
│   ├── dispute_reporter.py     # Dispute report generation
│   └── word_exporter.py        # Word document export
├── utils/                      # Utilities
│   ├── terminology_manager.py  # Terminology glossary management
│   ├── context_optimizer.py    # Token optimization utilities
│   └── metadata_store.py       # Document metadata persistence
└── config/                     # Configuration
    ├── prompts/                # LLM prompt templates
    └── settings.py             # System settings
```

### 3.2 Data Flow

```
User Input → Requirement Chat → Outline Generation → User Confirmation
                                            ↓
                    Web Crawling ← User Uploads → Source Ranking
                                            ↓
                    Metadata Extraction (Terminology + Style)
                                            ↓
                    Parallel Chapter Generation + Hallucination Guard
                                            ↓
                    Cross-Chapter Consistency Check
                                            ↓
                    Dispute Report Generation
                                            ↓
                    Plagiarism Detection
                                            ↓
                    Markdown Assembly → Word Export
                                            ↓
                    User Review → Partial Edit (loop back if needed)
```

## 4. Key Technical Decisions

### 4.1 Diagram Generation
- **Selected Tool**: Mermaid
- **Rationale**: Text-based, version-controllable, widely supported in Markdown renderers
- **Output Format**: Mermaid code blocks in Markdown, rendered at display time

### 4.2 Plagiarism Detection
- **Selected Tool**: Python `difflib`
- **Rationale**: Built-in, no external dependencies, sufficient for segment-level similarity
- **Algorithm**: `SequenceMatcher.ratio()` for similarity score

### 4.3 Hallucination Review Output Format
```json
{
    "status": "pass|fail|warning",
    "issues": [
        {
            "type": "hallucination|inconsistency|unsupported_claim",
            "location": "paragraph_index",
            "content": "problematic_text",
            "suggestion": "correction_suggestion"
        }
    ],
    "retry_recommended": true|false
}
```

### 4.4 Document Metadata Schema
```json
{
    "document_profile": {
        "type": "tutorial|manual|paper|handbook|api_doc|guide",
        "granularity": "overview|standard|comprehensive|deep_dive",
        "target_audience": "...",
        "tone": "technical|tutorial|academic",
        "tense": "present",
        "person": "third|second"
    },
    "terminology_glossary": {
        "term_key": {
            "primary": "Standard Term",
            "aliases": ["Alt1", "Alt2"],
            "definition": "..."
        }
    },
    "chapter_summaries": {
        "ch1": "Chapter 1 summary...",
        "ch2": "Chapter 2 summary..."
    },
    "cross_references": {
        "concept_x": "ch1/sec2/para3"
    }
}
```

## 5. Output Specifications

### 5.1 Primary Output
- **Format**: Markdown with YAML frontmatter
- **Features**:
  - Table of Contents (auto-generated)
  - Mermaid diagram support
  - Proper heading hierarchy
  - Reference citations

### 5.2 Secondary Output
- **Format**: Microsoft Word (.docx)
- **Features**:
  - Preserved heading structure
  - Embedded Mermaid diagrams as images
  - Styled document with TOC

### 5.3 Dispute Report
- **Format**: Separate Markdown file
- **Naming**: `{document_name}_disputes.md`
- **Content Structure**:
  - Executive Summary
  - Conflict Items (numbered)
  - Resolution Recommendations

## 6. Next Steps

1. **Architecture Finalization**: Determine application type (Web/CLI/Desktop)
2. **AI Service Selection**: Choose primary LLM provider and fallback strategy
3. **Storage Strategy**: Define persistence layer (filesystem vs database)
4. **MVP Scope**: Identify minimum viable feature set for initial release
5. **Development Phasing**: Plan iterative development milestones

---

*Document generated from brainstorming session on 2026-03-19*
