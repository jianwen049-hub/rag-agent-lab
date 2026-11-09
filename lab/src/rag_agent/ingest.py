"""Load markdown docs → split → embed → persist into Chroma."""

from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rich.console import Console

from rag_agent.config import Settings, get_settings
from rag_agent.store import open_store, reset_store

console = Console()


def load_markdown_docs(data_dir: Path) -> list[Document]:
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    docs: list[Document] = []
    for path in sorted(data_dir.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(data_dir))
        docs.append(
            Document(
                page_content=text,
                metadata={"source": rel, "filename": path.name},
            )
        )
    return docs


def split_docs(
    docs: list[Document],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    """Recursive character splitter — good default for markdown prose + code fences."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", " ", ""],
        length_function=len,
    )
    return splitter.split_documents(docs)


def ingest(*, reset: bool = False, settings: Settings | None = None) -> int:
    """
    Build / rebuild the vector index from lab/data/*.md.

    Returns number of chunks written.
    """
    settings = settings or get_settings()
    if not settings.has_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or still the placeholder. "
            "Copy .env.example → .env and set a real key (or compatible gateway)."
        )

    if reset:
        console.print("[yellow]Resetting persist dir…[/yellow]", settings.persist_dir)
        reset_store(settings)

    raw = load_markdown_docs(settings.data_dir)
    if not raw:
        raise RuntimeError(f"No .md files under {settings.data_dir}")

    chunks = split_docs(
        raw,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    for d in raw:
        src = d.metadata.get("source", "?")
        n = sum(1 for c in chunks if c.metadata.get("source") == src)
        console.print(f"  • {src}: ~{n} chunks (raw {len(d.page_content)} chars)")

    store = open_store(settings)
    # Avoid duplicate piles on re-ingest without --reset: clear collection via reset.
    ids = store.add_documents(chunks)
    console.print(
        f"[green]Ingested {len(ids)} chunks[/green] → {settings.persist_dir} "
        f"(collection={settings.collection})"
    )
    return len(ids)


if __name__ == "__main__":
    ingest()
