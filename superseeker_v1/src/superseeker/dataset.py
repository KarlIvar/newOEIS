from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .interfaces import SequenceRepository
from .models import SequenceRecord


def _parse_terms(raw_terms: Any) -> tuple[int, ...]:
    if isinstance(raw_terms, list):
        tokens = raw_terms
    elif isinstance(raw_terms, str):
        tokens = [part.strip() for part in raw_terms.split(",")]
    else:
        return tuple()

    parsed: list[int] = []
    for token in tokens:
        try:
            parsed.append(int(str(token).strip()))
        except ValueError:
            continue
    return tuple(parsed)


class JsonlSequenceRepository(SequenceRepository):
    def __init__(self, dataset_path: Path):
        self._records: dict[str, SequenceRecord] = {}
        self._load(dataset_path)

    def _load(self, dataset_path: Path) -> None:
        with dataset_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                a_number = str(obj.get("a_number", ""))
                number = int(obj.get("number", 0))
                name = str(obj.get("name", ""))
                terms = _parse_terms(obj.get("terms", obj.get("data", "")))
                record = SequenceRecord(
                    a_number=a_number,
                    number=number,
                    name=name,
                    terms=terms,
                    keyword=str(obj.get("keyword", "")),
                    offset=str(obj.get("offset", "")),
                    extra={},
                )
                if a_number:
                    self._records[a_number] = record

    def all_records(self) -> list[SequenceRecord]:
        return list(self._records.values())

    def get(self, a_number: str) -> SequenceRecord | None:
        return self._records.get(a_number)
