"""Chroma vector store helpers — open, reset, as_retriever."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from rag_agent.config import Settings, get_settings

if TYPE_CHECKING:
    from langchain_core.vectorstores import VectorStoreRetriever


def build_embeddings(settings: Settings | None = None) -> OpenAIEmbeddings:
    settings = settings or get_settings()
    kwargs: dict = {
        "model": settings.embed_model,
        "api_key": settings.openai_api_key or None,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAIEmbeddings(**kwargs)


def open_store(settings: Settings | None = None) -> Chroma:
    """Open (or create) the persistent Chroma collection."""
    settings = settings or get_settings()
    settings.persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.collection,
        embedding_function=build_embeddings(settings),
        persist_directory=str(settings.persist_dir),
    )


def reset_store(settings: Settings | None = None) -> None:
    """Delete the on-disk persist directory. Next open_store() starts clean."""
    settings = settings or get_settings()
    if settings.persist_dir.exists():
        shutil.rmtree(settings.persist_dir)


def as_retriever(
    settings: Settings | None = None,
    *,
    k: int | None = None,
) -> VectorStoreRetriever:
    settings = settings or get_settings()
    store = open_store(settings)
    return store.as_retriever(search_kwargs={"k": k or settings.top_k})
