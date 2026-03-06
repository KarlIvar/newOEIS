from __future__ import annotations

from .models import QuerySequence


def identity(terms: tuple[int, ...]) -> tuple[int, ...]:
    return terms


def diff1(terms: tuple[int, ...]) -> tuple[int, ...]:
    if len(terms) < 2:
        return tuple()
    return tuple(terms[i + 1] - terms[i] for i in range(len(terms) - 1))


def diff2(terms: tuple[int, ...]) -> tuple[int, ...]:
    return diff1(diff1(terms))


def partial_sums(terms: tuple[int, ...]) -> tuple[int, ...]:
    out: list[int] = []
    total = 0
    for term in terms:
        total += term
        out.append(total)
    return tuple(out)


def default_transforms_for(query: QuerySequence) -> list[tuple[str, QuerySequence]]:
    base = query.terms
    candidates: list[tuple[str, tuple[int, ...]]] = [
        ("identity", identity(base)),
        ("diff1", diff1(base)),
        ("diff2", diff2(base)),
        ("partial_sums", partial_sums(base)),
    ]
    return [(name, QuerySequence(terms=terms, source=name)) for name, terms in candidates if terms]
