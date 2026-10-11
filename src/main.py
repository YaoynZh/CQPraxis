import argparse
import json
from pathlib import Path

from src.pipeline import GenerationPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Multi-agent cross-cultural item generation pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_one = subparsers.add_parser("run-one", help="Run the pipeline for a single seed")
    run_one.add_argument("--seed-id", required=True, help="Seed identifier to process")
    run_one.add_argument("--input", default="data/seed_ex.jsonl", help="Seed input JSONL path")
    run_one.add_argument(
        "--output-dir",
        help="Root directory for this run's outputs, logs, and rejected records",
    )
    run_one.add_argument("--task-types", nargs="+", choices=["A", "B", "C"], help="Restrict task types")
    run_one.add_argument("--mock-llm", action="store_true", help="Use built-in mock LLM responses")

    run_batch = subparsers.add_parser("run-batch", help="Run the pipeline for multiple seeds")
    run_batch.add_argument("--input", default="data/seed_ex.jsonl", help="Seed input JSONL path")
    run_batch.add_argument(
        "--output-dir",
        help="Root directory for this run's outputs, logs, and rejected records",
    )
    run_batch.add_argument(
        "--target-total-items",
        type=int,
        help="Reference size N used to compute equal coverage quotas",
    )
    run_batch.add_argument("--task-types", nargs="+", choices=["A", "B", "C"], help="Restrict task types")
    run_batch.add_argument(
        "--coverage-input",
        help="Optional full seed-pool path used to define domain and region coverage during retries",
    )
    run_batch.add_argument("--mock-llm", action="store_true", help="Use built-in mock LLM responses")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    output_root = Path(args.output_dir) if args.output_dir else None
    pipeline = GenerationPipeline(input_path=Path(args.input), output_root=output_root, mock_llm=args.mock_llm)

    if args.command == "run-one":
        result = pipeline.run_one(
            seed_id=args.seed_id,
            allowed_task_types=args.task_types,
        )
    else:
        result = pipeline.run_batch(
            target_total_items=args.target_total_items,
            allowed_task_types=args.task_types,
            coverage_input_path=Path(args.coverage_input) if args.coverage_input else None,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
