from __future__ import annotations

from .interfaces import CandidateRetriever, Ranker
from .models import Candidate, QuerySequence, RankedResult
from .transforms import default_transforms_for


class SuperSeekerPipeline:
    def __init__(self, retriever: CandidateRetriever, ranker: Ranker):
        self._retriever = retriever
        self._ranker = ranker

    def search(self, query: QuerySequence, top_k: int = 10, per_transform_k: int = 100) -> list[RankedResult]:
        all_candidates: list[Candidate] = []
        for _, transformed_query in default_transforms_for(query):
            all_candidates.extend(self._retriever.retrieve(transformed_query, top_k=per_transform_k))

        # Keep best base score per (sequence, transform) before final rerank.
        dedup: dict[tuple[str, str], Candidate] = {}
        for candidate in all_candidates:
            key = (candidate.a_number, candidate.transform_name)
            current = dedup.get(key)
            if current is None or candidate.base_score > current.base_score:
                dedup[key] = candidate

        return self._ranker.rank(query=query, candidates=list(dedup.values()), top_k=top_k)
