# rag-agent-lab

> An open **technical lab + blog** on RAG and tool-calling agents. The posts are the main thing; the `lab/` code is what they cite — clone it, run it, break it, then read why it's built this way.

Maintained by **马健文 / Evans Owen** — backend engineer (~3y Java) working deep in AI agents and RAG. Background: [`PROFILE.md`](./PROFILE.md).

Every post follows the same discipline: **问题 → 怎么做 → 为什么这样最好**, ending in real pitfalls (retrieval noise, tool loops, context overflow, silent hallucination) and what actually fixed them. All paths cited in the posts exist in this repo.

---

## Start here: the reading path

Four Chinese deep-dives that walk through the stack bottom-up. Each names the problem, compares options, and then walks the shipped code:

| # | Post (中文) | The engineering question |
|---|---|---|
| 01 | [RAG 检索质量：为什么「能搜到」不等于「答得对」](./docs/blog/01-rag-retrieval-quality.md) | Why does retrieval miss, and which knobs actually move it — chunking, separators, top-k, honest empty results |
| 02 | [Agent Tool Calling：让模型「决定何时动手」](./docs/blog/02-agent-tool-calling.md) | When should the model search vs compute; tool schemas, an AST-safe calculator, iteration limits vs tool loops |
| 03 | [向量数据库选型：lab 用 Chroma，生产该换什么、什么时候换](./docs/blog/03-vector-db-choice.md) | FAISS vs Chroma vs Qdrant/Milvus vs PGVector as a trade-off (quality × latency × ops), and the seam that makes swapping cheap |
| 04 | [LangChain 编排：Chain 何时够用，Agent 何时值得上](./docs/blog/04-langchain-orchestration.md) | Fixed chain vs tool-calling agent vs LangGraph state machine — control flow, cost, failure containment |

Index with per-post code anchors: [`docs/blog/README.md`](./docs/blog/README.md)

## The lab (what the posts cite)

A runnable **LangChain RAG + tool-calling agent** over a local markdown knowledge base:

- **Vector store**: Chroma persisted under `lab/.chroma/` — isolated behind `store.py`
- **Orchestration**: `create_tool_calling_agent` + `AgentExecutor(max_iterations=6)`
- **Tools**: `search_knowledge_base` (RAG with `source=` citations) + `calculator` (AST whitelist, no `eval`)
- **Knowledge base**: 4 Chinese markdown files under `lab/data/`

Design rules the lab follows (and the posts argue for):

1. **Evidence over vibes** — retrieval returns passages with `source=`; the agent must cite them or state the KB doesn't cover it.
2. **No `eval`** — the calculator is an AST-node whitelist; `scripts/smoke_check.py` asserts `__import__('os')` is rejected.
3. **One seam for the vector store** — `store.py` is the only file that knows Chroma exists; swapping to FAISS/Qdrant touches nothing else.
4. **Explicit rebuilds** — `ingest --reset` over silent upsert; source of truth stays in `lab/data/*.md`.
5. **Config via env, secrets never in the tree** — see `lab/.env.example`.

---

## Quick start

Requires Python 3.10+ and an OpenAI API key **or** any OpenAI-compatible endpoint (`OPENAI_BASE_URL`). No key ships with the repo; without one, `ingest`/`chat` fail at the API boundary by design.

```bash
cd lab
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit: set OPENAI_API_KEY (and optional base URL / models)
export PYTHONPATH=src       # Windows PowerShell: $env:PYTHONPATH="src"

python3 -m rag_agent.cli ingest                 # data/*.md → Chroma
python3 -m rag_agent.cli chat "什么是 RAG？它和微调有什么区别？"
python3 -m rag_agent.cli chat "帮我算一下 (128 + 64) * 0.15"   # agent picks the calculator
python3 -m rag_agent.cli repl                   # interactive loop
```

Structure check without an API key:

```bash
cd lab && export PYTHONPATH=src && python3 scripts/smoke_check.py
```

Full run steps, layout, troubleshooting table: [`lab/README.md`](./lab/README.md)

---

## 中文简介

约 3 年 Java 后端，现在主攻 **AI Agent / RAG** 工程。本仓库是一个面向公众的技术实验室 + 中文博客，不是名词堆砌：

1. **深度中文博客（本仓库的主角）**：每篇按「问题背景 → 目标 → 方案对比 → 最终设计 → 关键代码拆解 → 踩坑 → 可改进点」展开，覆盖检索质量、工具调用、向量库选型、编排取舍，全部引用仓库真实路径
2. **可运行的 lab**：本地向量库（Chroma）+ 文档检索工具 + AST 安全计算器 + LangChain tool-calling Agent，陌生人 clone 后 30 分钟内可按 README 跑通

---

## Repo layout

```
.
├── README.md                 # this file
├── PROFILE.md                # about the author
├── LICENSE                   # MIT
├── docs/blog/                # Chinese deep-dives (the main content)
│   ├── README.md             # index with per-post code anchors
│   ├── 01-rag-retrieval-quality.md
│   ├── 02-agent-tool-calling.md
│   ├── 03-vector-db-choice.md
│   └── 04-langchain-orchestration.md
└── lab/                      # runnable Python project
    ├── README.md             # full run steps + troubleshooting
    ├── requirements.txt      # pinned deps
    ├── .env.example          # config template — no secrets committed
    ├── data/                 # sample knowledge base (4 markdown files)
    ├── scripts/smoke_check.py
    └── src/rag_agent/        # package: config, ingest, store, tools, agent, cli
```

---

## License

MIT — see [`LICENSE`](./LICENSE).
