# Action Item Extractor
Turns unstructured meeting notes into validated,
structured action items - owner, task, deadline -
using Gemini, with a golden-set evaluation that
scores every field.
## Problem
Meeting notes bury commitments. Owners, tasks, and
deadlines sit inside paragraphs, implied or halfstated, and follow-up depends on someone re-reading
and re-typing them. This tool extracts them into
strict JSON - and refuses to invent a deadline the
notes never stated.

## How it works
1. Notes are fenced and sent to Gemini
(google.genai SDK) with a strict output schema.
2. Output is validated field by field. Invalid
output is retried with the validation error as
feedback.
3. eval.py scores the extractor against 5 handwritten golden cases - owner, task, and
deadline accuracy reported separately, so a
weak field is visible, not averaged away.

## Usage
Prerequisites: Python 3.12 and uv.
Get a free Gemini key at https://aistudio.google.com
git clone https://github.com/AntoinneS/ai-engineer-journey.git
cd ai-engineer-journey
uv sync
# Create .env (never committed):
# GEMINI_API_KEY=your-key-here
# GEMINI_MODEL=gemini-2.5-flash
uv run python -m pytest # deterministic tests
uv run python eval.py # scored golden-set run

## Evaluation
Golden-set baseline (v0.1, gemini-2.5-flash,
5 cases, [N] items):
| Field | Accuracy |
|----------|----------|
| Owner | [x]% |
| Task | [x]% |
| Deadline | [x]% |
Eval run cost: $[amount] ([n] calls).
Goldens live in goldens/ - hand-written expected
output, never generated from model output.

## Project structure
hello_llm.py First verified, cost-metered call
extract.py Plain-text extraction (Day 2)
extract_json.py Validated JSON extractor (Days 3-4)
eval.py Golden-set scorer (Day 5)
goldens/ 5 cases: notes + expected JSON
tests/ Deterministic tests - offline, no API

## Roadmap
- [x] Cost-metered Gemini call (Day 1)
- [x] Plain-text extraction (Day 2)
- [x] Validated structured JSON output (Day 3)
- [x] Hardened extractor: retry, timeout, cost (Day 4)
- [x] Golden-set eval + deterministic tests (Day 5)
- [x] v0.1: clean install verified, tagged (Day 6)
- [ ] Prompt engineering patterns
- [ ] RAG over real documents
- [ ] Tool-using agents
## What is next
Prompt patterns measured against this same golden
set - every change re-scored, kept or reverted on
the numbers, not on impressions.

Stack: Python 3.12 - uv - Gemini (google.genai)
