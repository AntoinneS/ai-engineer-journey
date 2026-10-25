# AI Engineer Journey

Applied AI engineering, built in public — LLM APIs, prompt engineering, RAG, agents, and evals. Every piece verified, cost-metered, and reproducible from the first commit.

## What's here

- **`hello_llm.py`** — first verified LLM API call (Google Gemini via the `google.genai` SDK). Prints the model's response **and** the token usage for every call: prompt tokens, response tokens, total. Cost visibility from call one, because every production LLM feature is a billing line item.
- **`pyproject.toml` / `uv.lock`** — reproducible Python 3.12 environment managed with `uv`. Clone it, sync it, it runs.
- **'extract.py'** — structured extraction from meeting notes into Owner | Task | Deadlinerows, driven by a system instruction plus a few-shot example. Run it against the sample input:uv run python extract.py notes.txt``

## Run it

```bash
git clone git@github.com:antoinnes/ai-engineer-journey.git
cd ai-engineer-journey
uv sync

# API key (free at https://aistudio.google.com) — never committed
echo "GEMINI_API_KEY=your-key-here" > .env

uv run python hello_llm.py
```

## Why start here

Most LLM demos skip the two things that matter in production: **what each call costs** and **whether the setup reproduces on another machine**. This repo starts with both nailed down. Everything that follows builds on the same discipline — same environment standard, same cost awareness, same "prove it runs" bar.

Day one also taught a production lesson the easy way: the first script 404'd because the model name it used had been retired. The fix wasn't a new name — it was reading the model from an environment variable so the next retirement doesn't break the code. Demos hardcode. Systems degrade gracefully.

Prompt tokens:   245
Response tokens: 49
Total tokens:    1040

## Roadmap

- [x] Foundation: Python 3.12, `uv`, Git, cost-metered first API call
- [x] Structured output: reliable JSON from the model
- [ ] Prompt engineering patterns
- [ ] RAG over real documents
- [ ] Tool-using agents with evals
- [ ] Cloud: AWS Bedrock (AIP-C01 track) — managed models, Guardrails, Knowledge Bases

## Stack

Python 3.12 · uv · Google Gemini (`google.genai`) · Git
