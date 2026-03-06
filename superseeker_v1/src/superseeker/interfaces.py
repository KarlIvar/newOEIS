from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from .models import Candidate, QuerySequence, RankedResult, SequenceRecord


class SequenceRepository(Protocol):
    def all_records(self) -> Iterable[SequenceRecord]:
        ...

    def get(self, a_number: str) -> SequenceRecord | None:
        ...


class CandidateRetriever(Protocol):
    def retrieve(self, query: QuerySequence, top_k: int) -> list[Candidate]:
        ...


class TransformEngine(Protocol):
    def transforms_for(self, query: QuerySequence) -> list[tuple[str, QuerySequence]]:
        ...


class Ranker(Protocol):
    def rank(
        self,
        query: QuerySequence,
        candidates: Sequence[Candidate],
        top_k: int,
    ) -> list[RankedResult]:
        ...


class Calibrator(Protocol):
    def calibrate(self, ranked_results: Sequence[RankedResult]) -> list[RankedResult]:
        ...
