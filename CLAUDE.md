# health-answer-evals

Evaluation harness measuring how often LLM answers to health questions are unsafe,
with confidence intervals and inter-rater agreement. See `README.md` for the
design rationale and `rubric.md` for the scoring definitions.

## Stack
- Python 3.11, pandas, matplotlib, pytest
- No database; CSV in, CSV and Markdown out

## Layout
- `data/questions.csv`: versioned question set (`question_id`, `risk_tier`)
- `src/generate.py`: collects model answers, anonymises them, emits a blank label sheet
- `src/metrics.py`: pure statistics — Wilson intervals, Cohen's kappa
- `src/report.py`: adjudication, `results/report.md`, chart
- `tests/test_metrics.py`: unit tests for the statistics

## Commands
- Install: `pip install -r requirements.txt`
- Collect answers: `python -m src.generate --provider mock`
- Build report: `python -m src.report --labels labels/<sheet>.csv`
- Tests: `python -m pytest tests/ -q`
- Format and lint: `black . && ruff check .`

## Rules (always follow)
- NEVER commit API keys. Providers read `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
  from the environment only.
- NEVER edit `results/response_key.csv` into the labelling flow — it maps
  `response_id` to model and would break blind labelling.
- Statistics changes in `src/metrics.py` require a test with a hand-computed
  expected value, not a value copied from the implementation's own output.
- Do not report a proportion without its confidence interval. At n=40 a bare
  point estimate is misleading.
- Do not average `harmful_advice` across raters. Disagreements there are
  adjudicated individually; `report.py` takes the worst case.
- `data/questions.csv` is versioned data: add questions, do not silently reword
  existing ones, or historical labels stop being comparable.
- Synthetic labels (`labels/example_labels_synthetic.csv`) are for pipeline
  demonstration only. Never present numbers derived from them as findings.

## Code style
- Format with Black, lint with Ruff.
- Type hints on new code; small, pure functions in `metrics.py` so they stay testable.
- Any new metric gets a unit test covering a worked example and an edge case
  (n small, p=0, p=1).

## Working with AI-generated changes
- Explain the plan before multi-file changes.
- Run `pytest` after changes and report the result.
- Flag anything touching the rubric, the question set, or the blinding logic for
  human review — those change what the numbers mean, not just how they are computed.
- When adding health questions, do not invent clinical thresholds. Cite a
  guideline (HSE, NHS, NICE, WHO) in `expected_behaviour` or leave it for review.
