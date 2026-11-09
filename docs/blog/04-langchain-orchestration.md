# 04 · LangChain 编排：Chain 何时够用，Agent 何时值得上

> 对应代码：`lab/src/rag_agent/agent.py` · `lab/src/rag_agent/cli.py` · `lab/src/rag_agent/prompts/system.txt` · `lab/README.md`

## 问题背景

「会用 LangChain」这个词已经通胀。工程上真正要回答的是：

- 你什么时候用 **固定 Chain**，什么时候上 **Agent**？  
- 编排层和业务工具层怎么切？  
- 失败时如何止损（重试、迭代上限、用户可见错误）？  
- 如果不用 LangChain，你自己会怎么抽象？

本篇把本 lab 的编排讲清楚：不是贴一张架构图，而是对着能跑的入口函数拆。

## 目标

1. 用最少概念跑通：**ingest →（可选）agent chat**  
2. 编排代码集中在 `agent.py`，CLI 只负责 IO  
3. 说清与 LangGraph 的边界：本 lab 有意不引入，但知道何时该升级  

## 方案对比

| 方案 | 控制流 | 可测性 | 成本 | 适用 |
|------|--------|--------|------|------|
| 纯手写 OpenAI API | 完全自控 | 高（你写多少测多少） | 低框架税 | 极简服务 |
| LangChain LCEL Chain | 固定 DAG | 高 | 中 | 标准 RAG 问答 |
| **Tool-calling AgentExecutor** | 模型动态选工具 | 中 | 中高 | **多动作、意图混杂** |
| LangGraph 状态机 | 显式节点/边 | 高（可画图） | 高 | 多步业务、人机回环、持久会话 |
| 重型多 Agent 框架 | 角色分工 | 视实现 | 很高 | 复杂研究任务 |

本 lab 选择 **Tool-calling AgentExecutor**：

- 知识检索与计算两种动作已经够展示「动态路由」  
- 比一上来 LangGraph 更少概念负担，README 更好写  
- 仍使用官方推荐的 tool calling，而不是脆弱的 ReAct 字符串解析  

## 最终设计

```
cli.py
  ├─ ingest  → ingest.py → store.py
  ├─ chat    → agent.run_query
  └─ repl    → loop → agent.run_query

agent.py
  ├─ build_llm()          ChatOpenAI (base_url 可换)
  ├─ tools[]              search + calculator
  ├─ system prompt file   prompts/system.txt
  └─ AgentExecutor        max_iterations=6, verbose=True
```

设计原则：

1. **CLI 无业务**：不在 `cli.py` 里拼 Prompt  
2. **Prompt 外置文本文件**：方便非 Python 同事改语气  
3. **配置单例入口** `get_settings()`：12-factor 习惯，密钥不进仓库  
4. **verbose 默认开**：可观测优先于安静日志  

## 关键代码拆解

### 1) Agent 工厂 — `lab/src/rag_agent/agent.py`

`build_agent()` 完成四件事：校验 API Key → 建 LLM → 注册工具 → 绑 Prompt → 包 Executor。

`run_query(question)` 对 CLI 暴露「字符串进、字符串出」，后续接 FastAPI 也可以直接复用。

温度 `temperature=0.2`：工具选型场景更偏确定性；创意写作再另开配置。

### 2) CLI — `lab/src/rag_agent/cli.py`

子命令：

```bash
python -m rag_agent.cli ingest [--reset]
python -m rag_agent.cli chat "……"
python -m rag_agent.cli repl
```

`chat` 用 Rich Panel 区分 user / agent，方便截图进博客或 issue。

### 3) 系统提示词 — `lab/src/rag_agent/prompts/system.txt`

把「何时检索、何时计算、何时组合、空检索怎么办」写成可执行规则。  
**编排不只是 Python**：提示词是控制流的一部分——这点常被低估。

### 4) 和 Chain 版 RAG 的对比

若问题永远是「基于知识库问答」、无其它动作：  
用 LCEL `retriever | prompt | llm` 更便宜、更稳。  

一旦出现计算器、工单 API、数据库查询——继续堆 Chain 分支不如 Agent；  
一旦出现「检索 → 自评不足 → 换 query 再检索 → 人工确认」——再上 LangGraph。

## 踩坑

1. **为了用框架而用框架**  
   三个文件能讲清的链路，不必上多 Agent。展示「判断力」比展示「依赖树」重要。

2. **AgentExecutor 默认参数不审就上生产**  
   `max_iterations`、超时、回调、tracing（LangSmith）都要有意识。本 lab 显式写了迭代上限。

3. **在 notebook 里写完无法复现**  
   所以提供 `python -m` 入口与 `scripts/smoke_check.py`（无 Key 也能验包结构与计算器）。

4. **系统提示词与工具 description 漂移**  
   改了一个忘了另一个，表现为偶发乱调。改工具时两处一起改，PR 里当 checklist。

5. **把 API Key 写进 README 截图**  
   只用 `.env.example` 占位；`.gitignore` 忽略 `.env`。

## 可改进点

- [ ] 提供平行实现：`chain_rag.py` 固定链 vs `agent.py`，用同一评测集对比质量/费用  
- [ ] 接入 LangGraph：节点 = retrieve / grade / generate / calculate  
- [ ] OpenTelemetry 或 LangSmith tracing，可展示一次调用瀑布图  
- [ ] FastAPI 薄封装：`POST /chat`，把 lab 从 CLI 推到服务  
- [ ] 会话记忆：`ChatMessageHistory` 或外部 Redis，演示多轮指代  

## 系列收束

| 篇 | 问题 | 你应能讲清 |
|----|------|------------|
| [01](./01-rag-retrieval-quality.md) | 检索为什么不准 | 分块、top-k、空结果、重建索引 |
| [02](./02-agent-tool-calling.md) | 何时调工具 | schema、安全计算、迭代上限 |
| [03](./03-vector-db-choice.md) | 向量库怎么选 | 量级、过滤、适配层 |
| [04](./04-langchain-orchestration.md) | 怎么编排 | Chain vs Agent vs Graph |

回到仓库根目录 README，按 `lab/README.md` 跑通后，把本系列当作本 lab 的设计文档来读。
