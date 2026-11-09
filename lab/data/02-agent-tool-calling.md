# Agent 与 Tool Calling

## Agent 是什么

在工程语境里，Agent ≈ **带决策循环的 LLM**：

1. 观察用户目标  
2. 选择是否调用工具 / 调用哪个工具  
3. 把工具结果再喂回模型  
4. 直到给出最终答案或达到步数上限  

这和「单次 Prompt → 单次 Completion」的 Chain 不同：Agent 允许**多步、分支、纠错**。

## Tool Calling 的本质

现代 Chat 模型支持 **结构化函数调用**（function / tool calling）：

- 模型输出的不是自由文本「我要搜一下」，而是 JSON 风格的 `tool_name + arguments`
- 运行时真正执行函数，把返回值作为 `tool` 消息塞回对话
- 模型再基于证据续写

本 lab 注册了两个工具：

| 工具名 | 用途 | 实现 |
|--------|------|------|
| `search_knowledge_base` | 语义检索本地 Markdown 知识库 | `lab/src/rag_agent/tools/search.py` |
| `calculator` | 安全四则运算（AST，禁止 `eval`） | `lab/src/rag_agent/tools/calculator.py` |

## 什么时候该调工具

- **知识问题** → 检索，不要瞎编文档内容  
- **算术问题** → 计算器，不要让模型口算长式子  
- **组合问题** → 可以先检索概念，再对例子里的数字调用 calculator  

系统提示词约束见：`lab/src/rag_agent/prompts/system.txt`。

## 失败模式

1. **该调不调**：提示词太弱 / 工具 description 含糊  
2. **不该调乱调**：工具过多、描述重叠  
3. **死循环**：工具报错但 Agent 反复重试 → 需要 `max_iterations` 与错误回传  
4. **参数胡填**：缺 schema / 缺 few-shot 示例  

本 lab 用 LangChain `create_tool_calling_agent` + `AgentExecutor(max_iterations=6)` 做了硬上限。

详见：`docs/blog/02-agent-tool-calling.md`。
