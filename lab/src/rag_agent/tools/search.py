"""Knowledge-base search tool backed by the Chroma retriever."""

from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from rag_agent.config import get_settings
from rag_agent.store import as_retriever


class SearchInput(BaseModel):
    query: str = Field(..., description="Natural-language search query over the KB")


def _search_impl(query: str) -> str:
    settings = get_settings()
    retriever = as_retriever(settings)
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant passages found in the knowledge base."

    parts: list[str] = []
    for i, doc in enumerate(docs, start=1):
        src = doc.metadata.get("source", "unknown")
        parts.append(f"[{i}] source={src}\n{doc.page_content.strip()}")
    return "\n\n---\n\n".join(parts)


def build_search_tool() -> StructuredTool:
    """Factory so the tool closes over current settings at call time."""
    return StructuredTool.from_function(
        func=_search_impl,
        name="search_knowledge_base",
        description=(
            "Semantic search over the local markdown knowledge base (RAG). "
            "Use for questions about RAG, agents, vector DBs, LangChain, or any "
            "topic covered in lab/data. Returns top passages with source paths. "
            "Do NOT use for pure arithmetic."
        ),
        args_schema=SearchInput,
    )


# Default instance for agent wiring
search_knowledge_base = build_search_tool()
