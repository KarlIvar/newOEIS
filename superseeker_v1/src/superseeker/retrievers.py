from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .dataset import JsonlSequenceRepository
from .interfaces import CandidateRetriever, Ranker, SequenceRepository
from .models import Candidate, QuerySequence, RankedResult


def _prefix_overlap_score(query_terms: tuple[int, ...], candidate_terms: tuple[int, ...]) -> float:
    if not query_terms or not candidate_terms:
        return 0.0
    match = 0
    total = min(len(query_terms), len(candidate_terms))
    for i in range(total):
        if query_terms[i] != candidate_terms[i]:
            break
        match += 1
    return match / len(query_terms)


def _candidate_views(candidate_terms: tuple[int, ...]) -> list[tuple[str, tuple[int, ...]]]:
    """Return candidate sequence views, including slice projections."""
    views: list[tuple[str, tuple[int, ...]]] = [("a[:]", candidate_terms)]

    if len(candidate_terms) >= 2:
        even_terms = candidate_terms[0::2]
        odd_terms = candidate_terms[1::2]
        views.append(("a[0::2]", even_terms))
        if odd_terms:
            views.append(("a[1::2]", odd_terms))

    return views


class TermOverlapRetriever(CandidateRetriever):
    """Baseline retriever: score by exact prefix overlap of transformed terms."""

    def __init__(self, repo: SequenceRepository):
        self._repo = repo

    def retrieve(self, query: QuerySequence, top_k: int) -> list[Candidate]:
        scored: list[Candidate] = []
        for record in self._repo.all_records():
            best_score = 0.0
            best_view = "a[:]"
            for view_name, view_terms in _candidate_views(record.terms):
                score = _prefix_overlap_score(query.terms, view_terms)
                if score > best_score:
                    best_score = score
                    best_view = view_name

            if best_score <= 0:
                continue
            scored.append(
                Candidate(
                    a_number=record.a_number,
                    base_score=best_score,
                    evidence=f"prefix_overlap={best_score:.3f}; candidate_view={best_view}",
                    transform_name=query.source,
                )
            )
        scored.sort(key=lambda c: c.base_score, reverse=True)
        return scored[:top_k]


class SimpleRanker(Ranker):
    """Starter ranker: combine best candidate score per sequence across transforms."""

    def rank(self, query: QuerySequence, candidates: list[Candidate], top_k: int) -> list[RankedResult]:
        by_id: dict[str, list[Candidate]] = defaultdict(list)
        for candidate in candidates:
            by_id[candidate.a_number].append(candidate)

        ranked: list[RankedResult] = []
        for a_number, items in by_id.items():
            best = max(items, key=lambda item: item.base_score)
            transform_bonus = 0.05 if best.transform_name != "identity" else 0.0
            score = min(1.0, best.base_score + transform_bonus)
            ranked.append(
                RankedResult(
                    a_number=a_number,
                    score=score,
                    confidence=score,
                    evidence=f"{best.evidence}; transform={best.transform_name}",
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]


def build_baseline_components(dataset_path: str | Path) -> tuple[JsonlSequenceRepository, TermOverlapRetriever, SimpleRanker]:
    repo = JsonlSequenceRepository(dataset_path=Path(dataset_path))
    retriever = TermOverlapRetriever(repo)
    ranker = SimpleRanker()
    return repo, retriever, ranker
