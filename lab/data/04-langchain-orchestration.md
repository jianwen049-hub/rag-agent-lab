# LangChain 编排：从 Chain 到 Agent

## Chain：固定管道

经典 RAG Chain：

`question → retrieve → stuff documents → llm → answer`

优点：路径清晰、易测、成本可控。  
缺点：不会「自己决定」要不要检索、要不要算一下、检索失败后换策略。

## Agent：带工具的决策循环

当产品需要：

- 多种动作（搜文档 / 查库 / 调内部 API / 计算）  
- 用户意图多变  

就适合 **Tool-calling Agent**：模型在每一步选择工具或直接答。

本 lab 编排入口：`lab/src/rag_agent/agent.py`

- `ChatOpenAI` + `create_tool_calling_agent`  
- `AgentExecutor(verbose=True, max_iterations=6)`  
- CLI：`lab/src/rag_agent/cli.py`（`ingest` / `chat` / `repl`）

## 为什么本 lab 用 LangChain

1. **生态成熟**：文档、社区与真实案例最多，Retriever / Tool 抽象经过大规模验证  
2. **工具与 Retriever 抽象统一**，博客能对着真实路径拆  
3. 需要更强状态机时可演进到 **LangGraph**（本 lab 刻意保持简单可跑）

## 编排时的工程底线

- 提示词与工具 description 一致（否则模型乱选）  
- 限制迭代次数，防止账单与死循环  
- 检索空结果要显式处理  
- 密钥只走环境变量（见 `lab/.env.example`）  

详见：`docs/blog/04-langchain-orchestration.md`。
