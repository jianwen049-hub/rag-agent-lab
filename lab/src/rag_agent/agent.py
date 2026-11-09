"""Build a tool-calling LangChain agent over RAG search + calculator."""

from __future__ import annotations

from pathlib import Path

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from rag_agent.config import Settings, get_settings
from rag_agent.tools import calculator, build_search_tool

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.txt"


def load_system_prompt() -> str:
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def build_llm(settings: Settings | None = None) -> ChatOpenAI:
    settings = settings or get_settings()
    kwargs: dict = {
        "model": settings.chat_model,
        "temperature": 0.2,
        "api_key": settings.openai_api_key or None,
    }
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return ChatOpenAI(**kwargs)


def build_agent(settings: Settings | None = None) -> AgentExecutor:
    """
    Tool-calling agent:
      - search_knowledge_base  → Chroma RAG
      - calculator             → safe arithmetic AST eval
    """
    settings = settings or get_settings()
    if not settings.has_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing or still the placeholder. "
            "Copy lab/.env.example → lab/.env and set a real key."
        )

    llm = build_llm(settings)
    tools = [build_search_tool(), calculator]

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", load_system_prompt()),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=6,
    )


def run_query(question: str, settings: Settings | None = None) -> str:
    executor = build_agent(settings)
    result = executor.invoke({"input": question})
    return str(result.get("output", ""))
