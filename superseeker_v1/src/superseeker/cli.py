from __future__ import annotations

import argparse
import json
from pathlib import Path

from .dataset import JsonlSequenceRepository
from .evaluation import evaluate_pipeline, make_prefix_samples
from .models import QuerySequence
from .pipeline import SuperSeekerPipeline
from .retrievers import SimpleRanker, TermOverlapRetriever


def _parse_terms(text: str) -> tuple[int, ...]:
    out: list[int] = []
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(int(token))
    return tuple(out)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SuperSeeker v1 baseline CLI")
    parser.add_argument("--dataset", type=Path, required=True, help="Path to OEIS JSONL dataset.")
    parser.add_argument("--query", default="", help="Comma-separated query terms.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of ranked results.")
    parser.add_argument("--evaluate", action="store_true", help="Run offline evaluation mode.")
    parser.add_argument("--samples", type=int, default=200, help="Number of evaluation samples.")
    parser.add_argument("--prefix-len", type=int, default=8, help="Prefix length for synthetic eval queries.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo = JsonlSequenceRepository(args.dataset)
    pipeline = SuperSeekerPipeline(TermOverlapRetriever(repo), SimpleRanker())

    if args.evaluate:
        samples = make_prefix_samples(repo, sample_count=args.samples, prefix_len=args.prefix_len)
        report = evaluate_pipeline(pipeline, samples, top_k=args.top_k)
        print(
            json.dumps(
                {
                    "sample_count": report.sample_count,
                    "top1": report.top1,
                    "top10": report.top10,
                    "mrr": report.mrr,
                },
                indent=2,
            )
        )
        return 0

    if not args.query.strip():
        raise SystemExit("Provide --query or use --evaluate.")

    query = QuerySequence(terms=_parse_terms(args.query))
    ranked = pipeline.search(query, top_k=args.top_k)
    for idx, item in enumerate(ranked, start=1):
        print(f"{idx:02d} {item.a_number} score={item.score:.4f} confidence={item.confidence:.4f} {item.evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
