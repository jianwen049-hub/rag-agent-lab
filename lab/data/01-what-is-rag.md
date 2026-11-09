# 什么是 RAG（Retrieval-Augmented Generation）

## 一句话

RAG = **先检索再生成**：把外部知识库里相关的片段塞进 Prompt，让大模型基于证据回答，而不是只靠参数记忆。

## 为什么需要它

- 模型训练截止日之后的知识：产品文档、内部 Wiki、制度规章。
- 需要**可引用出处**的场景：客服、合规、技术支持。
- 不想为每一批新文档做一次全量微调。

## 和微调（Fine-tuning）的区别

| 维度 | RAG | Fine-tuning |
|------|-----|-------------|
| 知识更新 | 改索引即可 | 需重新训练 / 对齐 |
| 可解释性 | 能指向 source chunk | 黑盒参数 |
| 成本形态 | 检索 + 推理 | 训练算力 + 数据标注 |
| 擅长 | 事实问答、长尾文档 | 风格、格式、领域口语 |

实践中常见组合：**微调管行为与格式，RAG 管事实**。

## 典型流水线

1. **Ingest**：加载文档 → 清洗 → 分块（chunk）→ Embedding → 写入向量库  
2. **Retrieve**：用户问题 → Embedding → top-k 相似片段（可加 rerank / 元数据过滤）  
3. **Augment + Generate**：拼 Prompt（系统说明 + 检索片段 + 问题）→ LLM 作答  

本 lab 的实现入口：

- 入库：`lab/src/rag_agent/ingest.py`
- 检索工具：`lab/src/rag_agent/tools/search.py`
- 编排：`lab/src/rag_agent/agent.py`

## 质量关键不在「会不会调 API」

真正拉开差距的是：

- 分块策略是否破坏语义（标题、列表、代码块）
- top-k 与相似度阈值是否合理
- 是否把「检索不到」诚实地告诉用户，而不是幻觉补全

详见博客：`docs/blog/01-rag-retrieval-quality.md`。
