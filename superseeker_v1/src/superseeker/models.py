from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SequenceRecord:
    a_number: str
    number: int
    name: str
    terms: tuple[int, ...]
    keyword: str = ""
    offset: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QuerySequence:
    terms: tuple[int, ...]
    source: str = "user"


@dataclass(frozen=True)
class Candidate:
    a_number: str
    base_score: float
    evidence: str
    transform_name: str = "identity"


@dataclass(frozen=True)
class RankedResult:
    a_number: str
    score: float
    confidence: float
    evidence: str


@dataclass(frozen=True)
class EvaluationSample:
    query: QuerySequence
    expected_a_number: str


@dataclass(frozen=True)
class EvaluationReport:
    top1: float
    top10: float
    mrr: float
    sample_count: int
