"""Environment-driven settings for the lab. No secrets hardcoded."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env from cwd (typically lab/) if present.
load_dotenv()

_LAB_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_base_url: str | None
    chat_model: str
    embed_model: str
    data_dir: Path
    persist_dir: Path
    collection: str
    top_k: int
    chunk_size: int
    chunk_overlap: int

    @property
    def has_api_key(self) -> bool:
        return bool(self.openai_api_key) and not self.openai_api_key.startswith(
            "sk-your-key"
        )


def get_settings() -> Settings:
    data = os.getenv("RAG_DATA_DIR", str(_LAB_ROOT / "data"))
    persist = os.getenv("RAG_PERSIST_DIR", str(_LAB_ROOT / ".chroma"))
    base = os.getenv("OPENAI_BASE_URL") or None
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_base_url=base,
        chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
        embed_model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        data_dir=Path(data).expanduser().resolve(),
        persist_dir=Path(persist).expanduser().resolve(),
        collection=os.getenv("RAG_COLLECTION", "rag_lab_kb"),
        top_k=int(os.getenv("RAG_TOP_K", "4")),
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "500")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "80")),
    )
