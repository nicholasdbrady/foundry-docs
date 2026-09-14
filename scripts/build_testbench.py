#!/usr/bin/env python3
"""Build search evaluation testbench from feedback JSONL."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FEEDBACK_FILE = PROJECT_ROOT / "telemetry" / "feedback.jsonl"
OUTPUT_FILE = PROJECT_ROOT / "tests" / "search_testbench.json"


def _normalize_expected_path(value: str) -> str:
    path = value.strip().lstrip("/")
    if path.startswith("docs/"):
        path = path[len("docs/"):]
    if path.endswith(".mdx"):
        path = path[:-4]
    return path


def main():
    if not FEEDBACK_FILE.exists():
        raise FileNotFoundError(f"Feedback file not found: {FEEDBACK_FILE}")

    cases = {}
    with FEEDBACK_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            event = json.loads(raw)
            query = event.get("query", "").strip()
            expected = event.get("expected_result", "").strip()
            if not query or not expected:
                continue
            expected = _normalize_expected_path(expected)
            key = (query, expected)
            if key not in cases:
                cases[key] = {
                    "user_request": event.get("user_request", ""),
                    "query": query,
                    "expected_paths": [expected],
                    "min_results": 1,
                }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = list(cases.values())
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload)} test cases to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
