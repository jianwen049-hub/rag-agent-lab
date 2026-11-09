# rag-agent-lab

Runnable **RAG + tool-calling agent** backing the blog posts in [`../docs/blog/`](../docs/blog/).

- Vector store: **Chroma** (local persist under `.chroma/`)
- Orchestration: **LangChain** `create_tool_calling_agent` + `AgentExecutor`
- Tools: `search_knowledge_base` (RAG) + `calculator` (safe arithmetic)
- Knowledge: markdown files under `data/`

Blog posts cite real paths in this package — keep them in sync when you change code.

## Prerequisites

- Python 3.10+
- An OpenAI API key **or** any OpenAI-compatible endpoint (`OPENAI_BASE_URL`)

No key is shipped. Without a key, `ingest` / `chat` will fail at the API boundary (by design).

## Setup

```bash
cd lab
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# edit .env → set OPENAI_API_KEY (and optional BASE_URL / models)
```

Make sure the package is importable (src layout):

```bash
export PYTHONPATH=src              # Windows PowerShell: $env:PYTHONPATH="src"
# or: pip install -e .  if you add a pyproject later
```

## Exact run steps

### 1) Ingest sample docs → Chroma

```bash
cd lab
export PYTHONPATH=src
python3 -m rag_agent.cli ingest
```

Expected: chunk counts printed for each markdown under `data/`, then a persisted Chroma dir at `.chroma/`.

### 2) One-shot Q&A (agent decides tools)

```bash
python3 -m rag_agent.cli chat "什么是 RAG？它和微调有什么区别？"
python3 -m rag_agent.cli chat "帮我算一下 (128 + 64) * 0.15"
python3 -m rag_agent.cli chat "知识库里关于 Agent 循环和工具选择有哪些要点？"
```

### 3) Interactive REPL

```bash
python3 -m rag_agent.cli repl
```

Type `exit` / `quit` to leave.

### 4) Rebuild index after editing `data/`

```bash
python3 -m rag_agent.cli ingest --reset
```

## Layout

```
lab/
├── README.md
├── requirements.txt
├── .env.example
├── data/                      # sample knowledge base (≥3 md)
├── scripts/smoke_check.py     # offline import / structure check
└── src/rag_agent/
    ├── __init__.py
    ├── __main__.py            # python3 -m rag_agent
    ├── cli.py                 # ingest | chat | repl
    ├── config.py              # env-driven settings
    ├── ingest.py              # load → split → embed → persist
    ├── store.py               # Chroma open / reset helpers
    ├── agent.py               # tool-calling agent factory
    ├── prompts/
    │   └── system.txt
    └── tools/
        ├── __init__.py
        ├── search.py          # RAG retrieval tool
        └── calculator.py      # safe calculator tool
```

## Smoke check (no API key required)

```bash
cd lab
export PYTHONPATH=src
python3 scripts/smoke_check.py
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: rag_agent` | `export PYTHONPATH=src` from `lab/` |
| Auth / 401 from OpenAI | Check `OPENAI_API_KEY` and optional `OPENAI_BASE_URL` |
| Empty retrieval | Re-run `python3 -m rag_agent.cli ingest --reset` |
| Chroma lock / corrupt | Delete `lab/.chroma` and ingest again |

## Mapping to blog posts

| Post | Code |
|---|---|
| 01 Retrieval quality | `ingest.py`, `store.py`, `tools/search.py` |
| 02 Tool calling | `tools/*`, `agent.py` |
| 03 Vector DB choice | `store.py`, `config.py` |
| 04 Orchestration | `agent.py`, `cli.py`, `prompts/system.txt` |
