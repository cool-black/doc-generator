# Specs

This directory stores change-level specifications for DocGen.

These specs do not replace the project-level documents in the repository root or `docs/`.

Instead, they answer a different question:

- project docs explain what DocGen is, where it is going, and how it is built
- specs explain what a specific upcoming change will do, how it should behave, and how it will be validated

## When to Create a Spec

Create a spec when a change:

- affects product behavior in a meaningful way
- changes data models or storage
- changes CLI workflow
- introduces a new user-facing capability
- needs explicit scope and acceptance criteria

## Recommended Workflow

1. Align direction in `docs/PRODUCT_STRATEGY.md`
2. Reflect broader product intent in `product_spec.md`
3. Add or refine milestone planning in `docs/IMPLEMENTATION_PLAN.md`
4. Create a focused spec in `specs/`
5. Implement and test against that spec
6. Update `PROJECT_STATUS.md` and `CHANGELOG.md`

## Current Specs

- `spec-template.md` - reusable spec template
- `001-design-brief-clarification.md` - requirement clarification before outline generation
