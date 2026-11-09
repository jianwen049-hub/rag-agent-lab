# 技术博客（中文深拆）

每篇固定结构：**问题背景 → 目标 → 方案对比 → 最终设计 → 关键代码拆解 → 踩坑 → 可改进点**。  
文中路径均指向本仓库真实文件，请对照 `lab/` 阅读。

| # | 标题 | 代码锚点 |
|---|------|----------|
| [01](./01-rag-retrieval-quality.md) | RAG 检索质量 | `ingest.py` / `store.py` / `tools/search.py` |
| [02](./02-agent-tool-calling.md) | Agent Tool Calling | `tools/*` / `agent.py` / `prompts/system.txt` |
| [03](./03-vector-db-choice.md) | 向量库选型 | `store.py` / `config.py` |
| [04](./04-langchain-orchestration.md) | LangChain 编排 | `agent.py` / `cli.py` |

运行 lab：见 [`../../lab/README.md`](../../lab/README.md)。
