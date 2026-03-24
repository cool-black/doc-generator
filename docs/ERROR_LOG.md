# Error Log

Critical mistakes to avoid.

---

## #001: TDD Violation

**Date**: 2026-03-24
**Severity**: 🔴 High

### What Happened
Implemented M4 (Quality Review) without following TDD.

### Violation
```
❌ Wrong: Wrote implementation first
  - models/review.py
  - core/reviewer.py
  - llm/prompts/review.txt
  - Then added tests later

✅ Correct: Red-Green-Refactor
  - Write failing test first
  - Minimal implementation to pass
  - Refactor with tests passing
```

### Root Cause
- Defaulted to traditional "implement then test" pattern
- Saw TDD requirement in CLAUDE.md but didn't enforce it

### Prevention
**Before any code change:**
1. Check: Does test exist?
2. Run test: Does it fail (red)?
3. Only then: Write minimal implementation
4. Verify: Test passes (green)?

**Mandatory phrase:**
> "Per CLAUDE.md TDD requirements, I must write the test first. Let me create the test file and see it fail."

### Fix
- [x] Logged to ERROR_LOG.md
- [x] Fixed test enum values (DocumentType, Granularity)
- [x] All 21 tests passing
- [ ] Future: Always check model definitions before writing tests

---

## #002: Prompt Formatting Error

**Date**: 2026-03-24
**Severity**: 🔴 High

### What Happened
Runtime error when using review feature:
```
KeyError: '\n  "overall_score"'
```

### Root Cause
- Used `str.format()` with Jinja2-style template (`{{variable}}`)
- JSON example braces `{}` were interpreted as format placeholders

### Fix
- Changed `{{variable}}` → `{variable}` for Python format
- Escaped JSON braces: `{` → `{{`, `}` → `}}`

### Lesson
Test prompt templates with actual format() call before committing.

---

## #003: Temperature Parameter Error

**Date**: 2026-03-24
**Severity**: 🟡 Medium

### What Happened
HTTP 400 error during review:
```
invalid temperature: only 1 is allowed for this model
```

### Root Cause
Hardcoded `temperature=0.3` in reviewer.py, but some models (e.g., kimi-k2.5) only support `temperature=1`.

### Fix
Removed hardcoded temperature, use default from config instead.

### Lesson
Don't hardcode LLM parameters that may be model-specific.

---

## #004: Review Response Parse Failures

**Date**: 2026-03-24
**Severity**: 🔴 High

### What Happened
Multiple chapters failed review with parse errors:
```
Failed to parse review response: Expecting value: line 1 column 1 (char 0)
Chapter 4, 7, 8 review: FAIL (score: 0/100)
```

### Root Cause
1. LLM sometimes returns empty responses
2. JSON parser couldn't handle edge cases (partial JSON, extra text)
3. No fallback when JSON parsing fails

### Fix
1. Added empty response check at start of parser
2. Improved JSON extraction logic (handle markdown blocks better)
3. Added regex fallback to extract score from malformed responses
4. Better error logging with response preview
5. **Increased max_tokens 2000→4000** (root cause of empty responses)

### Files Changed
- `src/doc_gen/core/reviewer.py`: Enhanced `_parse_review_response()`, increased max_tokens
- `tests/test_reviewer.py`: Added tests for edge cases

### Lesson
Always handle edge cases in LLM response parsing:
- Empty responses (check max_tokens first!)
- Partial/malformed JSON
- Extra text wrapping JSON
- Add fallback mechanisms

**Key insight**: Empty responses often indicate insufficient max_tokens, not model errors.

---

*Log only critical errors. Keep it short.*
