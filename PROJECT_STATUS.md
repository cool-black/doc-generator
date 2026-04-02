# Project Status - DocGen

**Last Updated**: 2026-04-02
**Phase**: Usable MVP with product refocus underway
**Product Direction**: Technical tutorials, learning guides, and technical manuals

## 1. Executive Summary

DocGen is currently a functional CLI application that can generate complete Markdown documents through an outline-first, chapter-by-chapter workflow.

The current implementation is already usable for real document generation, with local project persistence, resume support, multi-provider LLM integration, and basic automated content review.

The next major shift is product refocus rather than core pipeline rescue:

- narrow the product around tutorial and learning-document generation
- improve requirement clarification before outlining
- add partial rewrite and feedback write-back
- improve content structure, source ingestion, and output richness

## 2. Verified Current Baseline

### Working End-to-End Flow

- Interactive runner via `python run.py`
- Manual CLI workflow via `python -m doc_gen ...`
- Project creation
- Outline generation and confirmation
- Sequential chapter generation
- Markdown export

### Verified Test Status

Local verification on 2026-04-02:

- `109 passed, 1 skipped`

## 3. Implemented Capabilities

| Capability | Status | Notes |
|------------|--------|-------|
| Project creation | Complete | Interactive prompts and local persistence |
| Outline generation | Complete | User-confirmed outline flow |
| Chapter generation | Complete | Sequential generation with context carry-over |
| Markdown export | Complete | TOC and final assembly |
| Resume / recovery | Complete | Can continue from previously generated chapters |
| Config validation | Complete | Better setup and error messaging |
| Multi-language support | Complete | 7 supported languages |
| Multi-provider LLM support | Complete | Includes OpenAI-compatible mode |
| Content review | Complete | Automated review with regeneration loop |
| Version history | Complete | Snapshot and rollback support |
| Token optimization | Complete | Context compression utilities |
| Web-source ingestion | Planned | Not yet implemented as a general feature |
| Partial rewrite | Planned | Not yet implemented |
| DOCX export | Planned | Not yet implemented |
| Style-template support | Planned | Not yet implemented |

## 4. Documentation and Product Alignment Status

The repository now has a clearer product direction, but code and UX are still transitioning toward it.

Alignment status:

- Product strategy has been refreshed
- Core entry documentation has been refreshed
- Product and project specifications have been rewritten to match the new direction
- Implementation still reflects the earlier broader product framing in some enums and prompts

## 5. Known Gaps

### Product Gaps

- Outline generation can still become too long or too broad
- Pre-outline clarification is still limited
- No native partial rewrite workflow yet
- No persistent editorial feedback model yet
- No source-connector system for web content yet
- Output style is still relatively plain

### Engineering Gaps

- CLI commands do not yet expose rewrite-oriented operations
- Source ingestion is still mostly file-parser based
- Export format is Markdown-only
- Architecture for style profiles and semantic tutorial blocks is not yet in place

## 6. Near-Term Priorities

### Priority 1: Product Focus

- reflect tutorial / learning-guide positioning consistently in prompts and docs
- reduce over-broad product framing

### Priority 2: Better Outline Inputs

- add requirement clarification workflow
- add design brief confirmation
- add outline constraints and optional module selection

### Priority 3: Revision Loop

- add chapter rewrite
- add section rewrite
- persist editorial feedback

### Priority 4: Richer Tutorial Output

- add learning roadmap and interview-highlights modules
- add semantic blocks such as notes, warnings, and summaries

## 7. Current Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Product scope drifts back to "generate anything" | High | Keep docs and roadmap focused |
| New rewrite flow introduces state complexity | High | Add explicit revision metadata and tests |
| Source support grows too fast | Medium | Add connector boundaries before broad ingestion |
| Output quality feels generic | Medium | Add tutorial modules and style guidance |

## 8. Recommended Next Milestone

The next milestone should focus on product-fit improvements rather than broad feature expansion:

1. requirement clarification before outlining
2. outline scope control
3. chapter/section rewrite
4. feedback persistence

These four changes would most directly improve the usefulness of first-generation output and reduce the need for manual rewriting outside the tool.
