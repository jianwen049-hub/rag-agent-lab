# 向量数据库怎么选

## 向量库在 RAG 里做什么

Embedding 模型把文本变成高维向量；向量库负责：

- **存储**向量 + metadata（source、标题、权限标签…）
- **近似最近邻（ANN）检索**（HNSW / IVF 等）
- （可选）过滤、混合检索、多租户

## 常见选项对比（工程视角）

| 方案 | 适合 | 优点 | 代价 |
|------|------|------|------|
| **FAISS** | 单机实验、批量召回 | 快、可控、无服务依赖 | 自己管持久化与并发 |
| **Chroma** | 本地原型、小团队 lab | API 友好、易持久化 | 大规模 / 多租户需评估 |
| **Milvus / Qdrant / Weaviate** | 生产、过滤复杂、水平扩展 | 运维能力与生态更强 | 部署与成本更高 |
| **云托管（PGVector / 厂商库）** | 已有云与合规约束 | 少运维 | 绑定与单价 |

## 本 lab 的选择：Chroma

理由（本地 lab 场景）：

1. **零服务**：`persist_directory` 落盘即可演示  
2. 与 LangChain 集成清晰（`langchain-chroma`）  
3. 足够支撑博客里讲「分块 / top-k / 重置索引」  

实现：`lab/src/rag_agent/store.py`（`open_store` / `reset_store` / `as_retriever`）。

若要改成 FAISS，通常只换 store 适配层，**ingest 分块与 Agent 工具层可以不动**——这是分层的意义。

## 选型检查清单

- 数据量级：万 / 百万 / 亿级向量？  
- 是否需要 metadata 强过滤（租户、ACL）？  
- 延迟 SLA 与是否要 hybrid（BM25 + 向量）？  
- 运维谁来做？能否接受本地文件锁？  

详见：`docs/blog/03-vector-db-choice.md`。
