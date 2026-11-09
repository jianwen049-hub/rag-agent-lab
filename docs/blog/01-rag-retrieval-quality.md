# 01 · RAG 检索质量：为什么「能搜到」不等于「答得对」

> 对应代码：`lab/src/rag_agent/ingest.py` · `lab/src/rag_agent/store.py` · `lab/src/rag_agent/tools/search.py` · `lab/data/`

## 问题背景

很多 Demo 的叙事是：接上 Embedding + 向量库 + `similarity_search`，RAG 就完成了。  
生产场景里，失败几乎都长这样：

- 用户问得很具体，召回的却是同主题的「正确废话」段落  
- 一个 Markdown 里标题、列表、代码挤在同一 chunk，相似度被噪声拉偏  
- top-k=4 固定不变：有的问题 1 段就够，有的要 8 段才拼得起答案  
- 检索为空时，模型仍然「很有自信」地编造

我有约 3 年 Java 后端经验，转到 AI 应用后最先补的不是「又一个框架」，而是把 **检索质量** 当成和接口延迟、事务一致性同级的工程问题。

## 目标

在本 lab 里落地一套**可解释、可重建**的本地 RAG：

1. 从 `lab/data/*.md` 入库，索引可 `--reset` 重建  
2. 分块参数显式可配（`RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP`）  
3. Agent 通过工具拿到带 `source=` 的原文片段，而不是黑盒「知识」  
4. 博客能指到真实路径，读者可以打开终端对照跑一遍

## 方案对比

| 方案 | 做法 | 优点 | 缺点 | 何时用 |
|------|------|------|------|--------|
| A. 整篇文档当 1 个向量 | 文件级 embedding | 实现极简 | 长文语义稀释，召回差 | 极短 FAQ |
| B. 固定长度硬切 | 每 N 字一切 | 好实现 | 切断句子/代码 | 快速探针 |
| C. 递归字符分割 + 标题优先分隔符 | `RecursiveCharacterTextSplitter` + `\n## ` 等 | 对 Markdown 友好，参数清晰 | 仍无结构感知 parser | **本 lab 选择** |
| D. 父子索引 / 小块召回大块生成 | 多级 chunk | 质量上限高 | 复杂度与存储上升 | 生产进阶 |
| E. 向量 + BM25 混合 + Rerank | hybrid + cross-encoder | 专有名词更稳 | 链路长、成本高 | 中文专名多、投诉驱动 |

选择 **C** 的原因：lab 要在「一晚能讲清楚 + 本机能跑」和「留出通往 D/E 的升级缝隙」之间取平衡。代码分层后，换成 D/E 只动检索层。

## 最终设计

```
data/*.md
   │  load_markdown_docs()
   ▼
Document(page_content, metadata.source)
   │  split_docs(chunk_size, chunk_overlap)
   ▼
chunks[]  ──embed──►  Chroma(persist_directory)
                           │
                           ▼
              search_knowledge_base(query) → top-k passages
```

关键决策：

1. **metadata 必带 `source`**：回答要能指回文件，展示「可引用」习惯  
2. **分隔符把 `##` / `###` 放前面**：尽量按小节切，而不是在段落中间砍  
3. **默认 chunk=500 / overlap=80**：中文 Markdown 经验起点，可用环境变量调  
4. **`--reset` 重建**：避免「重复 ingest 堆垃圾向量」这种 Demo 翻车

## 关键代码拆解

### 1) 加载与分块 — `lab/src/rag_agent/ingest.py`

```python
# load_markdown_docs: 每个 .md → Document，metadata.source = 相对路径
# split_docs: RecursiveCharacterTextSplitter
separators=["\n## ", "\n### ", "\n\n", "\n", "。", "；", " ", ""]
```

为什么把中文 `。` `；` 放进 separators？  
因为本 lab 知识库是**中文技术文**，只按空格切对中文几乎无意义；句号级回退能减少「半句开头」的丑 chunk。

`ingest(reset=...)` 在缺 key 时直接 `RuntimeError`，避免「 silently 写了空索引」。

### 2) 持久化与 Retriever — `lab/src/rag_agent/store.py`

- `open_store()`：`Chroma(collection_name, embedding_function, persist_directory)`  
- `as_retriever(k=top_k)`：工具层只依赖 Retriever 接口，不散落 Chroma API  

这是后面换 FAISS / Qdrant 的缝隙。

### 3) 检索工具如何把「证据」交回模型 — `lab/src/rag_agent/tools/search.py`

工具返回值不是 `Document` 对象，而是**格式化字符串**：

```text
[1] source=01-what-is-rag.md
<passage>

---

[2] source=...
```

模型在最终回答里更容易复述 `source=`，也方便你在 `verbose=True` 的 Agent 日志里肉眼验收召回是否离谱。

### 4) 配置 — `lab/src/rag_agent/config.py`

`RAG_TOP_K` / `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` 全部环境变量化：改完配置直接 `ingest --reset` 重建索引，就能肉眼观察「把 chunk 从 500 调到 200 之后召回怎么变」——这比背概念实在。

## 踩坑

1. **重复 ingest 不 reset**  
   Chroma 本地目录会堆积近似重复向量，表现为「怎么搜都像对，但又脏」。lab CLI 提供 `ingest --reset`。

2. **`PYTHONPATH` 忘记设**  
   src layout 下直接 `python -m rag_agent.cli` 会 `ModuleNotFoundError`。`lab/README.md` 写了 `export PYTHONPATH=src`。

3. **Chunk 过大**  
   一篇 02-agent 文档若整块塞进 top-1，模型会摘要过度，细节问答反而丢。先小后大。

4. **用聊天模型 embedding 维度心智混乱**  
   `OPENAI_EMBED_MODEL` 与 `OPENAI_CHAT_MODEL` 必须分开配；混用会在网关层直接 4xx。

5. **检索空结果仍让模型「自由发挥」**  
   工具层返回明确的 `No relevant passages...`，系统提示词要求承认未覆盖——见 `lab/src/rag_agent/prompts/system.txt`。

## 可改进点

- [ ] 增加 **BM25 混合检索**（中文专有名词：LangChain、Chroma 等）  
- [ ] chunk 级 **parent document**：小块召回，大块进 Prompt  
- [ ] 引入 **Reranker**（cross-encoder）只对 top-20 精排到 top-4  
- [ ] 简单离线评测集：10 个问题 + 期望 source，CI 里跑召回命中率  
- [ ] 按 `filename` / 标签做 metadata filter，模拟多租户知识库  

下一步阅读：[02 · Agent Tool Calling](./02-agent-tool-calling.md)
