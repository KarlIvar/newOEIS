from __future__ import annotations

import random

from .interfaces import SequenceRepository
from .models import EvaluationReport, EvaluationSample, QuerySequence
from .pipeline import SuperSeekerPipeline


def make_prefix_samples(
    repo: SequenceRepository,
    sample_count: int,
    prefix_len: int,
    seed: int = 7,
) -> list[EvaluationSample]:
    random.seed(seed)
    eligible = [record for record in repo.all_records() if len(record.terms) >= prefix_len]
    picked = random.sample(eligible, k=min(sample_count, len(eligible)))
    samples: list[EvaluationSample] = []
    for record in picked:
        query = QuerySequence(terms=record.terms[:prefix_len], source="eval_prefix")
        samples.append(EvaluationSample(query=query, expected_a_number=record.a_number))
    return samples


def evaluate_pipeline(
    pipeline: SuperSeekerPipeline,
    samples: list[EvaluationSample],
    top_k: int = 10,
) -> EvaluationReport:
    if not samples:
        return EvaluationReport(top1=0.0, top10=0.0, mrr=0.0, sample_count=0)

    top1_hits = 0
    top10_hits = 0
    reciprocal_sum = 0.0

    for sample in samples:
        ranked = pipeline.search(sample.query, top_k=top_k)
        rank = None
        for idx, item in enumerate(ranked, start=1):
            if item.a_number == sample.expected_a_number:
                rank = idx
                break

        if rank == 1:
            top1_hits += 1
        if rank is not None and rank <= 10:
            top10_hits += 1
            reciprocal_sum += 1.0 / rank

    count = len(samples)
    return EvaluationReport(
        top1=top1_hits / count,
        top10=top10_hits / count,
        mrr=reciprocal_sum / count,
        sample_count=count,
    )
