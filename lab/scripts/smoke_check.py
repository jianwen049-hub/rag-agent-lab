#!/usr/bin/env python3
"""Offline smoke check: imports + data files + safe calculator. No API key needed."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    errors: list[str] = []

    data = ROOT / "data"
    md_files = sorted(data.glob("*.md"))
    if len(md_files) < 3:
        errors.append(f"Need ≥3 markdown files in {data}, found {len(md_files)}")
    else:
        print(f"OK data: {len(md_files)} markdown files → {[p.name for p in md_files]}")

    from rag_agent.config import get_settings
    from rag_agent.tools.calculator import safe_calculate
    from rag_agent.ingest import load_markdown_docs, split_docs

    s = get_settings()
    print(f"OK config: data_dir={s.data_dir}")
    print(f"OK config: persist_dir={s.persist_dir}")

    assert safe_calculate("(128 + 64) * 0.15") == "28.8", safe_calculate("(128 + 64) * 0.15")
    assert safe_calculate("2 ** 10") == "1024"
    assert safe_calculate("__import__('os')").startswith("Error")
    print("OK calculator")

    docs = load_markdown_docs(s.data_dir)
    chunks = split_docs(docs, chunk_size=s.chunk_size, chunk_overlap=s.chunk_overlap)
    print(f"OK ingest path: {len(docs)} docs → {len(chunks)} chunks (no embed)")

    prompt = (SRC / "rag_agent" / "prompts" / "system.txt").read_text(encoding="utf-8")
    assert "search_knowledge_base" in prompt
    assert "calculator" in prompt
    print("OK system prompt")

    # Ensure agent module imports without calling API
    import rag_agent.agent  # noqa: F401
    import rag_agent.cli  # noqa: F401
    print("OK agent/cli import")

    if errors:
        for e in errors:
            print("FAIL:", e)
        return 1
    print("All smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
