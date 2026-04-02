# 001 - Design Brief Clarification

## 1. Summary

Add a requirement-clarification step before outline generation so DocGen can create a structured design brief and use that brief as the basis for a better, more focused outline.

## 2. Background

Today, DocGen generates outlines mainly from the initial project fields such as topic, document type, audience, and granularity.

This is workable for a generic draft, but it is not strong enough for the product direction DocGen is moving toward.

Current pain points:

- outlines can become too long or too broad
- the system does not know whether the user wants an intro guide, a systematic guide, or interview prep
- the system cannot reliably infer whether to emphasize concepts, practice, roadmap content, or examples
- project setup feels closer to field collection than real requirement clarification

Because of this, the first outline often requires more manual correction than it should.

## 3. Goals

- gather better tutorial-design inputs before outline generation
- generate a concise design brief from clarified user intent
- require user confirmation of the design brief before generating the formal outline
- persist the design brief as project data for reuse in later generation and revision flows

## 4. Non-Goals

- full rewrite support
- web-source ingestion
- style-template support
- section-level rewrite

These may reuse the design brief later, but they are not part of this spec.

## 5. User Experience

When a user starts a new project or begins outline generation, DocGen should ask a small set of additional questions such as:

- what is the document mainly for
- what level is the intended reader
- should it be compact, standard, or in-depth
- should it focus more on concepts or practical application
- should it include modules such as roadmap, interview highlights, glossary, or recap

After these questions, DocGen should produce a concise design brief.

Example design brief content:

- target audience
- learning goal
- content mode
- selected learning modules
- preferred balance of concept vs practice
- recommended outline scope

The user should then be able to:

- confirm the brief
- regenerate the brief
- cancel

Only after confirmation should DocGen move on to full outline generation.

## 6. Functional Requirements

- DocGen must support collecting additional clarification inputs before outline generation
- DocGen must generate a structured design brief object from those inputs
- DocGen must persist the design brief per project
- DocGen must use the design brief in outline prompt construction
- DocGen must require explicit confirmation before using the design brief to produce the final outline
- If a design brief already exists, DocGen should allow reuse or regeneration

## 7. Data Model and Storage Changes

### New Data Model

Add a `DesignBrief` model with fields such as:

- `goal_type`
- `audience_level`
- `learning_mode`
- `focus_mode`
- `selected_modules`
- `scope_guidance`
- `notes`

### Project-Level Integration

Either:

- embed a brief reference in `ProjectConfig`

or:

- persist the brief separately and keep project metadata lightweight

Recommended approach:

- persist a dedicated `design_brief.json` file in the project directory

### Storage Changes

Add helper functions in project storage for:

- save design brief
- load design brief
- detect whether a design brief exists

## 8. CLI / Interface Changes

### Interactive Runner

`run.py` should:

- ask clarification questions after the existing project setup step or during outline preparation
- present a generated design brief
- ask the user whether to confirm, regenerate, or cancel

### Command Workflow

The command-based flow should support the same behavior when generating outlines.

At minimum:

- `generate <name> --stage outline` should trigger the clarification/design-brief flow if no confirmed brief exists

Potential future command:

- `doc-gen brief <name>`

This future command is not required in the first implementation.

## 9. Implementation Notes

Suggested file areas:

- `src/doc_gen/models/project.py`
- `src/doc_gen/cli/prompts.py`
- `src/doc_gen/cli/commands.py`
- `run.py`
- `src/doc_gen/core/outline.py`
- `src/doc_gen/storage/project.py`

Suggested implementation approach:

1. add a `DesignBrief` model
2. add storage helpers for `design_brief.json`
3. add clarification prompt helpers
4. add a design-brief generation step before outline generation
5. inject brief fields into the outline prompt

Implementation should preserve the existing happy path for users who want the interactive workflow.

## 10. Acceptance Criteria

- users answer additional clarification questions before outline generation
- DocGen generates a structured design brief and shows it before the outline
- users can confirm or regenerate the brief
- confirmed briefs are persisted per project
- outline generation uses the design brief rather than relying only on the original project fields
- existing project generation flow still works end to end

## 11. Testing Plan

- unit tests for `DesignBrief` model defaults and serialization
- storage tests for saving and loading `design_brief.json`
- tests for outline prompt composition including design-brief content
- command/workflow tests for confirm and regenerate paths
- regression tests ensuring existing outline flow is not broken

## 12. Risks

- too many clarification questions may make the workflow feel heavy
- design brief generation may duplicate information already stored in `ProjectConfig`
- state handling may become confusing if a brief exists but is stale

Mitigation:

- keep the question set short and high-signal
- clearly separate raw project inputs from interpreted design brief
- allow regenerate and reuse flows explicitly

## 13. Out of Scope Follow-Ups

- outline constraint model expansion
- rewrite command
- editorial feedback persistence
- source connectors
- style-template extraction
