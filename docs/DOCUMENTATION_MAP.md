# Documentation Map

This file defines the intended documentation structure for the DocGen repository.

## 1. Top-Level Documents

### `README.md`

Audience:

- first-time visitors
- contributors
- evaluators

Purpose:

- explain what DocGen is
- show current positioning
- provide quick start
- link to the rest of the docs

### `product_spec.md`

Audience:

- product owner
- designer
- contributors discussing feature scope

Purpose:

- define product scope
- describe user problems and requirements
- record roadmap and non-goals

### `project_spec.md`

Audience:

- engineers
- maintainers

Purpose:

- describe architecture
- explain module boundaries
- document future extension points

### `PROJECT_STATUS.md`

Audience:

- maintainers
- collaborators

Purpose:

- record the current implementation baseline
- list verified capabilities
- summarize immediate gaps and priorities

### `CHANGELOG.md`

Audience:

- maintainers
- release readers

Purpose:

- record notable changes over time

## 2. `docs/` Directory

### `docs/PRODUCT_STRATEGY.md`

Purpose:

- long-term product direction
- positioning decisions
- strategic reasoning behind roadmap changes

### `docs/IMPLEMENTATION_PLAN.md`

Purpose:

- translate product direction into executable engineering work
- define delivery slices and file-level task areas

### `docs/TDD_WORKFLOW.md`

Purpose:

- engineering workflow guidance
- test-first development expectations

### `docs/ERROR_LOG.md`

Purpose:

- capture important implementation mistakes and lessons learned

### `docs/DOCUMENTATION_MAP.md`

Purpose:

- define the documentation system itself
- prevent overlap between docs

## 3. Non-Core Document Areas

### `specs/`

Purpose:

- store change-level specifications
- define scope, behavior, and acceptance criteria for individual feature waves

These specs complement the project-level docs. They should be used when implementing meaningful new capabilities.

### `.claude/CLAUDE.md`

Purpose:

- AI-assistant working guidance for this repository

It should stay aligned with the current product direction and documentation index, but it is not the main user-facing product documentation.

### `documents/`

Purpose:

- generated sample outputs
- reference artifacts for evaluating content quality

These are product artifacts, not project-governance docs.

## 4. Maintenance Rules

- `README.md` should stay concise and onboarding-focused
- `product_spec.md` should describe product intent, not low-level code details
- `project_spec.md` should describe implementation structure, not become a changelog
- `PROJECT_STATUS.md` should reflect verified facts and recent priorities only
- `CHANGELOG.md` should not be used as a roadmap
- strategy changes should first land in `docs/PRODUCT_STRATEGY.md`, then be propagated to core docs

## 5. Recommended Future Additions

When the next feature wave lands, consider adding:

- `docs/REVISION_WORKFLOW.md` for partial rewrite and feedback flow
- `docs/SOURCE_CONNECTORS.md` for supported source types and extraction rules
- `docs/STYLE_TEMPLATES.md` for style-reference or template guidance
