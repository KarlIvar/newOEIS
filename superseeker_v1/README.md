# SuperSeeker V1 Scaffold

This folder provides a concrete starting layout for a SuperSeeker-style system:

- ingestion from OEIS JSONL
- transform-aware candidate generation
- pluggable retrievers/rankers
- offline evaluation metrics (Top-1, Top-10, MRR)

## Suggested Layout

```text
superseeker_v1/
  README.md
  pyproject.toml
  src/superseeker/
    __init__.py
    models.py
    interfaces.py
    dataset.py
    transforms.py
    retrievers.py
    pipeline.py
    evaluation.py
    cli.py
    ui_server.py
    ui/index.html
```

## Quick Start

From `/Users/ivarangquist/Documents/code/godot-proj/superseeker_v1`:

```bash
python3 -m superseeker.cli \
  --dataset /Users/ivarangquist/Documents/code/godot-proj/oeis_first_5000.jsonl \
  --query "0,1,1,2,3,5,8,13,21,34" \
  --top-k 10
```

Evaluation on synthetic prefix queries:

```bash
python3 -m superseeker.cli \
  --dataset /Users/ivarangquist/Documents/code/godot-proj/oeis_first_5000.jsonl \
  --evaluate \
  --samples 200 \
  --prefix-len 8 \
  --top-k 10
```

Run the local web UI:

```bash
python3 -m superseeker.ui_server \
  --dataset /Users/ivarangquist/Documents/code/godot-proj/oeis_first_5000_unique.jsonl \
  --host 127.0.0.1 \
  --port 8765
```

Then open `http://127.0.0.1:8765`.

## What Is Implemented

- core dataclasses and protocols for pluggable components
- basic transform registry (identity, diff1, diff2, partial_sums)
- baseline retriever (`TermOverlapRetriever`) for term overlap scoring
- pipeline that merges transform candidates, then reranks
- evaluation harness for Top-1/Top-10/MRR

## Next Steps

1. Replace baseline retriever with BM25 + dense retrieval.
2. Add transform graph beam search.
3. Add feature-based ranker (GBDT or pairwise model).
4. Add confidence calibration on validation data.
