# CQGen

CQGen is the multi-agent framework used to construct CQPraxis, a benchmark for evaluating Contextual Cultural Alignment (CCA): whether large language models can identify subtle cultural cues in specific contexts and make culturally appropriate judgments and responses. Guided by Cultural Intelligence (CQ) theory, CQGen uses a moderator and four CQ experts to select an appropriate task format and CQ dimension for each cultural seed, jointly generate an item, validate its quality, and control the distribution of the final candidate pool.

## Method

For each cultural seed, CQGen follows five steps:

1. A moderator evaluates the cultural seed across Task A, B, and C and selects the most suitable task type.
2. Four CQ experts assess the seed from the metacognitive, cognitive, motivational, and behavioural dimensions, and the highest-scoring expert is selected.
3. The moderator and the selected CQ expert jointly generate an item based on the cultural seed, task type, and CQ dimension.
4. A validator checks seed grounding, CQ alignment, task-format validity, and answer coherence.
5. Validated items enter the candidate pool, and generation continues until the task–CQ, cultural-domain, and regional distribution requirements are satisfied.

CQGen supports three task formats:

- **Task A:** multiple-choice decision item
- **Task B:** dialogue-based appropriateness judgment
- **Task C:** open-ended scenario with a scoring rubric

## Data

- `data/seed_ex.jsonl` contains 10 representative, source-grounded seed examples covering 10 cultural domains and all six regions.
- `data/CQPraxis.jsonl` contains 1,080 generated benchmark items: 360 Task A, 360 Task B, and 360 Task C items.

## Setup

Python 3.9 is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Real item generation and semantic validation require access to an OpenAI-compatible chat-completions API. Copy `.env.example` to `.env` and provide `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`.

## Quick Start

Run a smoke test without external API calls. Mock mode verifies the pipeline and output format but does not perform real model-based generation or semantic evaluation.

```bash
python3 -m src.main run-one \
  --seed-id AS_001 \
  --input data/seed_ex.jsonl \
  --output-dir data/smoke_test \
  --mock-llm
```

Run one item with the configured API and model:

```bash
python3 -m src.main run-one \
  --seed-id AS_001 \
  --input data/seed_ex.jsonl
```

Run batch generation with a private seed file:

```bash
python3 -m src.main run-batch \
  --input /path/to/private_seeds.jsonl \
  --target-total-items 300
```

`target-total-items` is a reference size used to calculate equal-coverage quotas. The validated candidate pool may contain more than this number because generation stops only after the configured task–CQ, cultural-domain, and regional coverage conditions are all satisfied.

## Outputs

By default, CQGen writes:

- accepted items to `data/outputs/`
- rejected items to `data/rejected/`
- decisions, expert scores, validation traces, and runtime logs to `data/logs/`

## Project Structure

- `src/pipeline.py`: end-to-end generation pipeline
- `src/agents/`: moderator, CQ experts, item generator, and item-design rules
- `src/llm/`: model client, prompts, and participant skills
- `src/models/`: seed, decision, and item schemas
- `src/validators/`: deterministic and semantic quality validation
- `src/stats/`: distribution tracking and stopping conditions
- `configs/`: model, generation, and distribution settings
