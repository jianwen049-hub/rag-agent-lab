# 02 · Agent Tool Calling：让模型「决定何时动手」，而不是串一条死链

> 对应代码：`lab/src/rag_agent/tools/` · `lab/src/rag_agent/agent.py` · `lab/src/rag_agent/prompts/system.txt`

## 问题背景

只会做「问题 → 检索 → 生成」的流水线，很快会被一个现实问题追问：

> 用户有时问知识，有时问计算，有时两者都要——你的系统怎么分流？

如果答案是「我再加一个 if 分类器」，也可以，但扩展到第 5、第 6 个动作时，规则树会爆炸。  
Tool Calling Agent 的价值是：**把路由决策交给带 schema 的模型，把执行权留在你写的 Python 里**。

另一类翻车更隐蔽：Demo 里把 `eval()` 塞进计算器工具，看起来能跑，安全审查一眼否决。

## 目标

1. 至少两个真实工具：**文档检索** + **安全计算器**  
2. 工具 description / args schema 写到模型能稳定选对  
3. 系统提示词与工具职责对齐，减少「该搜却口算、该算却检索」  
4. 有迭代上限，防止工具报错时死循环刷 token  

## 方案对比

| 方案 | 思路 | 优点 | 缺点 |
|------|------|------|------|
| 规则路由 | 正则/分类模型先判意图再进不同 Chain | 可控、便宜 | 意图一多就崩；难组合 |
| 单次 ReAct 纯文本 | 让模型输出 `Thought/Action` 字符串再解析 | 老写法，资料多 | 解析脆，易格式跑飞 |
| **原生 Tool Calling** | 模型产出结构化 tool call | 稳定、与官方 API 对齐 | 依赖模型能力 |
| 多 Agent 分工 | Planner / Researcher / Critic | 复杂任务上限高 | lab 过重、成本高 |

本 lab 选 **原生 Tool Calling + AgentExecutor**：与官方 API 的 function calling / tool use 语义对齐，代码量适合深拆。

## 最终设计

```
User question
    │
    ▼
ChatOpenAI (tool-calling)
    │  decides
    ├─► search_knowledge_base(query)  → Chroma passages
    ├─► calculator(expression)        → AST-safe number
    └─► (no tool) final answer
    │
    └─ loop until final / max_iterations=6
```

约束写在两处，必须同时存在：

1. **工具 description**（模型选工具时读）  
2. **system prompt**（模型规划时读）——`lab/src/rag_agent/prompts/system.txt`

只写一处，运行中很容易复现「偶发乱调」。

## 关键代码拆解

### 1) 安全计算器 — `lab/src/rag_agent/tools/calculator.py`

核心思想：**允许的 AST 节点白名单**，绝不用 `eval` / `exec`。

```python
_BIN_OPS = {ast.Add: op.add, ast.Sub: op.sub, ...}
# 只接受 Constant / BinOp / UnaryOp
# Pow 再加简单幅度限制，避免 9**99 这类坑
```

`@tool` 装饰后的 `calculator(expression: str)` docstring 会进入工具 schema——所以 docstring 里写清了「算术用我，知识题别用我」。

### 2) 检索工具 — `lab/src/rag_agent/tools/search.py`

使用 `StructuredTool.from_function` + Pydantic `SearchInput`：

- `name="search_knowledge_base"` 稳定，不随函数重命名乱飘  
- description 明确：**语义检索本地 Markdown；纯算术不要用**  
- 返回带 `source=` 的文本，方便最终回答引用  

`build_search_tool()` 工厂方法让每次 Agent 构建拿到当前配置（top_k、persist 路径），避免测试时闭包脏状态。

### 3) 组装 Agent — `lab/src/rag_agent/agent.py`

```python
tools = [build_search_tool(), calculator]
prompt = ChatPromptTemplate.from_messages([
    ("system", load_system_prompt()),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])
agent = create_tool_calling_agent(llm, tools, prompt)
AgentExecutor(..., verbose=True, max_iterations=6, handle_parsing_errors=True)
```

`agent_scratchpad` 是 Tool Calling 中间态（tool call + tool result）的占位；没有它，多步工具调不起来。

### 4) 可观测性

`verbose=True` 会在终端打印工具选择与入参——调试或演示时能直接看到「这一步它选了 calculator 而不是检索」，路由是否正确一目了然。CLI 见 `lab/src/rag_agent/cli.py`。

## 踩坑

1. **工具描述互相抢戏**  
   若两个工具都写「可以帮助用户解决问题」，模型会随机。职责要互斥、例子要具体。

2. **`eval` 计算器**  
   安全上直接不可接受。用 AST 白名单；并在 `scripts/smoke_check.py` 断言 `__import__('os')` 失败。

3. **忘记 max_iterations**  
   工具一直报错时，Agent 可能反复重试 → 账单与日志爆炸。本 lab 固定 `6`。

4. **Prompt 说「必须先检索」导致算术题也先搜**  
   系统提示词改成「知识题优先检索；纯算术走 calculator；可组合」，见 `prompts/system.txt`。

5. **把 Retriever 硬绑进 Chain，又声称自己是 Agent**  
   一问「不检索行不行」就露馅。本 lab 的检索是**工具**，模型可以不调。

## 可改进点

- [ ] 增加第三个工具：例如 `get_datetime` 或「读取某个配置键」，展示扩展方式  
- [ ] Tool 级超时与重试策略（对外部 HTTP 工具尤其重要）  
- [ ] 把 verbose 日志结构化落盘，做「工具选择准确率」统计  
- [ ] 对 calculator 支持单位换算 / 百分比文字题的轻量解析  
- [ ] 升级到 LangGraph：显式状态机画「检索 → 反思 → 再检索」  

下一步阅读：[03 · 向量库选型](./03-vector-db-choice.md)
