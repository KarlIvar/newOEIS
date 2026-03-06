from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .dataset import JsonlSequenceRepository
from .evaluation import evaluate_pipeline, make_prefix_samples
from .models import QuerySequence
from .pipeline import SuperSeekerPipeline
from .retrievers import SimpleRanker, TermOverlapRetriever


class AppState:
    def __init__(self, dataset_path: Path):
        self.repo = JsonlSequenceRepository(dataset_path)
        self.pipeline = SuperSeekerPipeline(TermOverlapRetriever(self.repo), SimpleRanker())
        self.dataset_size = len(self.repo.all_records())


def parse_terms(text: str) -> tuple[int, ...]:
    cleaned = text.replace("\n", ",")
    values: list[int] = []
    for token in cleaned.split(","):
        token = token.strip()
        if not token:
            continue
        values.append(int(token))
    return tuple(values)


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=True).encode("utf-8")


def build_handler(state: AppState, ui_root: Path) -> type[BaseHTTPRequestHandler]:
    class SuperSeekerUIHandler(BaseHTTPRequestHandler):
        app_state = state
        static_root = ui_root

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_file(self, status: int, path: Path, content_type: str) -> None:
            body = path.read_bytes()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0:
                return {}
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            if parsed.path in ("/", "/index.html"):
                index_path = self.static_root / "index.html"
                self._send_file(200, index_path, "text/html; charset=utf-8")
                return

            if parsed.path == "/api/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "dataset_size": self.app_state.dataset_size,
                    },
                )
                return

            self._send_json(404, {"error": "Not found"})

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            try:
                payload = self._read_json_body()
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON body."})
                return

            if parsed.path == "/api/search":
                self._handle_search(payload)
                return

            if parsed.path == "/api/evaluate":
                self._handle_evaluate(payload)
                return

            self._send_json(404, {"error": "Not found"})

        def _handle_search(self, payload: dict[str, Any]) -> None:
            query_text = str(payload.get("query", ""))
            try:
                terms = parse_terms(query_text)
            except ValueError:
                self._send_json(400, {"error": "Query terms must be integers separated by commas."})
                return

            if not terms:
                self._send_json(400, {"error": "Provide at least one term."})
                return

            raw_top_k = payload.get("top_k", 10)
            try:
                top_k = max(1, min(50, int(raw_top_k)))
            except (TypeError, ValueError):
                self._send_json(400, {"error": "top_k must be an integer between 1 and 50."})
                return

            query = QuerySequence(terms=terms, source="ui")
            ranked = self.app_state.pipeline.search(query, top_k=top_k)
            results: list[dict[str, Any]] = []
            for index, item in enumerate(ranked, start=1):
                record = self.app_state.repo.get(item.a_number)
                results.append(
                    {
                        "rank": index,
                        "a_number": item.a_number,
                        "name": record.name if record else "",
                        "oeis_url": f"https://oeis.org/{item.a_number}",
                        "score": item.score,
                        "confidence": item.confidence,
                        "evidence": item.evidence,
                    }
                )

            self._send_json(
                200,
                {
                    "query_terms": list(terms),
                    "result_count": len(results),
                    "results": results,
                },
            )

        def _handle_evaluate(self, payload: dict[str, Any]) -> None:
            try:
                samples = max(1, min(2000, int(payload.get("samples", 200))))
                prefix_len = max(3, min(30, int(payload.get("prefix_len", 8))))
                top_k = max(1, min(50, int(payload.get("top_k", 10))))
            except (TypeError, ValueError):
                self._send_json(400, {"error": "samples, prefix_len and top_k must be integers."})
                return

            eval_samples = make_prefix_samples(
                self.app_state.repo,
                sample_count=samples,
                prefix_len=prefix_len,
            )
            report = evaluate_pipeline(
                self.app_state.pipeline,
                eval_samples,
                top_k=top_k,
            )
            self._send_json(
                200,
                {
                    "sample_count": report.sample_count,
                    "top1": report.top1,
                    "top10": report.top10,
                    "mrr": report.mrr,
                },
            )

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[ui] {self.address_string()} - {fmt % args}")

    return SuperSeekerUIHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the SuperSeeker v1 local web UI.")
    parser.add_argument("--dataset", type=Path, required=True, help="Path to OEIS JSONL dataset.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind.")
    parser.add_argument("--port", type=int, default=8765, help="Port to listen on.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state = AppState(args.dataset)
    ui_root = Path(__file__).resolve().parent / "ui"
    handler = build_handler(state, ui_root)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"SuperSeeker UI available at http://{args.host}:{args.port}")
    print(f"Loaded sequences: {state.dataset_size}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
