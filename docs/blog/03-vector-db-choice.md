# 03 · 向量数据库选型：lab 用 Chroma，生产该换什么、什么时候换

> 对应代码：`lab/src/rag_agent/store.py` · `lab/src/rag_agent/config.py` · `lab/src/rag_agent/ingest.py`

## 问题背景

「熟悉 Faiss / Milvus / Chroma / PGVector」这类描述很容易变成名词背诵。  
真选型时，先答上自己这几个问题：

- 你的数据量到哪一档？  
- 要不要 metadata 过滤（租户、权限）？  
- 索引坏了怎么重建？热更新怎么做？  
- 为什么 Demo 用 A，上线改 B，中间改了哪一层？

选型的本质不是「谁更潮」，而是 **检索质量 × 延迟 × 运维成本 × 组织约束** 的权衡。

## 目标

1. 在 lab 里用 **本地可持久化** 的向量存储跑通 RAG  
2. 把存储适配收敛到 `store.py`，ingest / tools / agent 不渗漏供应商 API  
3. 博客里给出一张可复用的对比表 + 升级路径  

## 方案对比

| 方案 | 部署形态 | 过滤 / 混合检索 | 运维 | 适合阶段 |
|------|----------|-----------------|------|----------|
| **FAISS** | 库内嵌 | 弱（常自建） | 低（但持久化/并发自己扛） | 算法实验、批量召回 |
| **Chroma** | 本地目录或轻服务 | 够用 | 极低 | **原型 / 本地 lab / 小知识库** |
| **Qdrant / Milvus / Weaviate** | 独立服务 | 强 | 中高 | 生产、多租户、规模化 |
| **PGVector** | 跟 Postgres 走 | SQL 友好 | 中（你已有 PG 时很香） | 业务库一体、事务友好 |
| 云厂商托管 | SaaS | 视产品 | 低运维高单价 | 合规与人力受限时 |

### 为什么不是 FAISS 作为本 lab 默认？

FAISS 很快，但「持久化 + 文档 metadata + LangChain Retriever」要写更多胶水。本 lab 首要目标是 **30 分钟内陌生人能按 README 跑通**，Chroma 的 `persist_directory` 心智负担更低。

### 为什么不是一上来 Milvus？

杀鸡用牛刀：Docker、资源、集合 schema、运维叙事会淹没「检索质量 / Agent 工具」主线。规模与过滤需求真上来了再迁，迁移缝隙见 `store.py` 的三函数边界。

## 最终设计

`lab/src/rag_agent/store.py` 只暴露三个动作：

| API | 含义 |
|-----|------|
| `open_store()` | 打开或创建集合，绑定 Embedding |
| `reset_store()` | 删除 `persist_dir`，允许干净重建 |
| `as_retriever(k=...)` | 返回 LangChain Retriever，供工具使用 |

配置项（`config.py`）：

- `RAG_PERSIST_DIR`（默认 `lab/.chroma`）  
- `RAG_COLLECTION`  
- `OPENAI_EMBED_MODEL`  

**分层**：`ingest.py` 只 `add_documents`；`tools/search.py` 只 `retriever.invoke`；它们不知道 Chroma 细节以外的东西——这就是以后换 Qdrant 的接口边界。

## 关键代码拆解

### 打开与重置 — `store.py`

```python
Chroma(
    collection_name=settings.collection,
    embedding_function=build_embeddings(settings),
    persist_directory=str(settings.persist_dir),
)
```

`reset_store` 直接 `shutil.rmtree(persist_dir)`：对本地 lab 足够；生产会改成「别名集合 + 原子切换」，博客里不装成已经做了。

### Embedding 构建

`build_embeddings` 同时吃 `api_key` 与可选 `base_url`，兼容官方 OpenAI 与兼容网关——后端出身的人会对「驱动可替换」更敏感。

### 和 ingest 的契约

`ingest --reset` → `reset_store` → `open_store` → `add_documents`。  
不提供「静默 upsert 去重」是有意的：在 lab 阶段，**显式重建**比「半自动去重但说不清主键」更诚实。

## 踩坑

1. **把向量库当业务数据库**  
   缺了备份、迁移、版本。至少要有「从源 Markdown 全量重建」的能力——本 lab 强制 source-of-truth 在 `lab/data/`。

2. **persist 路径写进容器临时层**  
   重启索引没了。配置里用明确目录，`.gitignore` 忽略 `.chroma/`。

3. **collection 名变了却还指向旧目录**  
   表现为「ingest 成功但检索像空的」。排查先看 `RAG_COLLECTION` 与 `RAG_PERSIST_DIR`。

4. **Embedding 模型更换后旧向量未重建**  
   不同模型向量空间不兼容。换 `OPENAI_EMBED_MODEL` 必须 `--reset`。

5. **只报参数名不报量级**  
   说清一句：当前 lab 是百级 chunk；万级可继续 Chroma/FAISS；百万级 + 复杂过滤再谈 Qdrant/Milvus/PGVector。

## 可改进点

- [ ] 增加 `store_faiss.py` 适配，CLI 用 `RAG_STORE=chroma|faiss` 切换  
- [ ] 集合版本号：`rag_lab_kb_v3`，检索挂到 current 别名  
- [ ] metadata：`tags` / `lang` / `acl` 字段，演示 filtered retrieval  
- [ ] 导出/导入：把 embeddings 与 ids 打成 parquet，便于迁移云库  
- [ ] 延迟与召回的简易 benchmark 脚本  

下一步阅读：[04 · LangChain 编排](./04-langchain-orchestration.md)
