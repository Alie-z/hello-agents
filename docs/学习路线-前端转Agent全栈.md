# 前端工程师转 Agent 全栈 12 周学习路线

这份路线面向已有前端、Node、Go 基础，Python 能看能改，并且已有可用 LLM API Key 的学习者。目标不是通读所有材料，而是把 `docs/` 章节、`code/` 示例和 Web 综合项目串成一条能落地的 Agent 全栈路径。

## 学习原则

- 每周投入 6-8 小时，按“读章节、跑示例、改代码、写笔记”的节奏推进。
- 中文文档为主，英文文档只在术语或翻译不清时对照。
- Python 不单独系统学习，在章节代码中补齐 FastAPI、Pydantic、虚拟环境、依赖管理。
- 第十一章训练内容只做理解和小样本实验，不把 GPU 训练作为主线。
- 优先级为 Agent 工程能力、框架 API 熟练度、模型训练能力。

## 每周固定交付

每周在 `docs/learning-notes/` 下新增一份笔记，建议命名为 `week01.md`、`week02.md`。笔记结构固定为：

- 核心概念
- 跑通代码
- 改造点
- 遇到的问题
- 可迁移到前端工程的启发

第 4、8、11、12 周必须有可运行 demo。每个 demo 至少记录启动命令、环境变量、核心截图或关键输出、失败兜底方式。

## 第 1-2 周：Agent 与 LLM 基础

阅读内容：

- [第一章 初识智能体](./chapter1/第一章%20初识智能体.md)
- [第二章 智能体发展史](./chapter2/第二章%20智能体发展史.md)
- [第三章 大语言模型基础](./chapter3/第三章%20大语言模型基础.md)

运行代码：

```bash
python code/chapter1/FirstAgentTest.py
python code/chapter2/ELIZA.py
python code/chapter3/BPE.py
python code/chapter3/Transformer.py
```

学习重点：

- 用前端工程视角理解 `Agent = LLM + 状态 + 工具 + 循环 + 环境`。
- 把 LLM 调用理解为远程 API，把 prompt 理解为接口协议的一部分。
- 观察最早期规则机器人和 LLM Agent 的区别：规则匹配、上下文、工具、行动循环。

交付物：

- 一张 Agent 运行模型图或文字说明，解释输入、状态、工具调用、输出之间的关系。
- 一份最小 Agent 术语表，包含 Agent、Tool、Memory、Prompt、Context、Observation、Action。

## 第 3-4 周：经典 Agent 范式

阅读内容：

- [第四章 智能体经典范式构建](./chapter4/第四章%20智能体经典范式构建.md)

运行代码：

```bash
cd code/chapter4
pip install -r requirements.txt
python ReAct.py
python Plan_and_solve.py
python Reflection.py
```

学习重点：

- ReAct：思考、行动、观察的循环。
- Plan-and-Solve：先规划，再分步执行。
- Reflection：执行后复盘并改进。
- 工具调用循环、失败重试、最大步数、防死循环。

改造任务：

- 把“根据用户需求生成页面 TODO”做成一个 ReAct 实验。
- 至少提供 3 个工具：需求拆解、组件建议、接口 mock 建议。
- 记录工具调用日志，观察 LLM 何时选择工具、何时直接回答。

第 4 周验收：

- demo 能用真实 LLM 跑通一次。
- demo 能展示至少一次工具调用。
- demo 有最大步数限制和工具失败提示。

## 第 5 周：低代码 Agent 平台速览

阅读内容：

- [第五章 基于低代码平台的智能体搭建](./chapter5/第五章%20基于低代码平台的智能体搭建.md)

学习重点：

- 把 Coze、Dify、n8n 理解为产品原型工具，不把它们作为主开发栈。
- 对比 workflow、tool、knowledge base、trigger、plugin 与代码 Agent 中的对应概念。
- 识别低代码适合的场景：快速验证、运营流程、非工程团队协作。

交付物：

- 一张低代码 Agent 和代码 Agent 的能力边界表。
- 记录 3 个“适合低代码”的任务和 3 个“必须代码实现”的任务。

## 第 6-7 周：Agent 框架与自研框架

阅读内容：

- [第六章 框架开发实践](./chapter6/第六章%20框架开发实践.md)
- [第七章 构建你的Agent框架](./chapter7/第七章%20构建你的Agent框架.md)

运行代码：

```bash
python code/chapter6/Langgraph/Dialogue_System.py

cd code/chapter7
python test_simple_agent.py
python test_my_calculator.py
python test_react_agent.py
python test_reflection_agent.py
python my_main.py
```

学习重点：

- 框架封装层次：LLM client、Agent class、ToolRegistry、history、streaming。
- AutoGen、AgentScope、LangGraph 的定位差异。
- 自研框架最小内核：`LLM -> Agent -> Tool -> Memory -> Runner`。

交付物：

- 写出 HelloAgents 最小内核说明：每个模块负责什么、输入输出是什么、依赖什么。
- 用 TypeScript 接口风格重写一版核心对象定义，帮助把 Python 类映射到前端熟悉的类型系统。

## 第 8 周：记忆、RAG 与上下文工程

阅读内容：

- [第八章 记忆与检索](./chapter8/第八章%20记忆与检索.md)
- [第九章 上下文工程](./chapter9/第九章%20上下文工程.md)

运行代码：

```bash
python code/chapter8/01_MemoryTool_Basic_Operations.py
python code/chapter8/10_RAG_Pipeline_Complete.py
python code/chapter9/01_context_builder_basic.py
```

学习重点：

- 短期记忆、长期记忆、向量检索、上下文压缩、结构化笔记。
- 上下文不是聊天记录堆叠，而是面向任务构建的输入包。
- RAG 的关键质量点：切分、召回、重排、引用、回答约束。

改造任务：

- 给一个 Agent 增加用户偏好记忆。
- 增加资料检索问答能力，回答中必须带引用来源或材料片段。

第 8 周验收：

- demo 能记住至少 2 条用户偏好。
- demo 能从一份本地资料中检索并回答问题。
- demo 能解释本次回答使用了哪些上下文。

## 第 9 周：MCP、A2A 与 Agent 协议

阅读内容：

- [第十章 智能体通信协议](./chapter10/第十章%20智能体通信协议.md)

运行代码：

```bash
python code/chapter10/02_Connect2MCP.py
python code/chapter10/05_UseMCPToolInAgent.py
python code/chapter10/07_SimpleA2AAgent.py
```

学习重点：

- MCP 是工具协议，解决 Agent 如何发现和调用外部能力。
- A2A 是 Agent 通信协议，解决多 Agent 间任务协作。
- ANP 偏服务发现和网络化协作，可作为扩展理解。

交付物：

- 设计一个“前端工具服务 -> MCP -> Agent 调用”的架构图。
- 额外思考如何用 Node 或 Go 写一个最小 MCP server，作为后续加分项。

## 第 10 周：评估与训练概览

阅读内容：

- [第十一章 Agentic-RL](./chapter11/第十一章%20Agentic-RL.md)
- [第十二章 智能体性能评估](./chapter12/第十二章%20智能体性能评估.md)

运行代码：

```bash
python code/chapter12/01_basic_agent_example.py
python code/chapter12/03_bfcl_custom_evaluation.py
```

学习重点：

- 评估优先于训练：先知道 Agent 哪里差，再决定是否优化 prompt、工具、上下文或模型。
- 核心指标：任务完成率、工具调用正确率、答案质量、延迟、成本。
- 训练章节只做概念和小样本理解，掌握 SFT、RL、GRPO 的位置即可。

交付物：

- 为自己的最终 Agent 项目设计 5-10 条验收测试集。
- 每条测试包含输入、期望行为、是否需要工具、通过标准。

## 第 11 周：Web Agent 综合案例

阅读内容：

- [第十三章 智能旅行助手](./chapter13/第十三章%20智能旅行助手.md)
- [第十四章 自动化深度研究智能体](./chapter14/第十四章%20自动化深度研究智能体.md)

运行项目：

```bash
cd code/chapter13/helloagents-trip-planner/backend
pip install -r requirements.txt
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

```bash
cd code/chapter14/helloagents-deepresearch/backend
pip install -e .
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

cd ../frontend
npm install
npm run dev
```

学习重点：

- Vue 3 + TypeScript 前端如何对接 FastAPI 后端。
- Pydantic schema 如何约束 Agent 输入输出。
- Agent 服务层如何组织 LLM、工具、搜索、状态和错误。
- 前端如何展示进度状态、引用来源、步骤日志、错误提示。

第 11 周验收：

- 至少一个 Web 项目前端 `npm run build` 通过。
- 后端能启动，核心 API 可在 Swagger 或浏览器中验证。
- 改造一个前端页面，增加步骤日志、引用来源或错误兜底中的至少两项。

## 第 12 周：毕业项目

阅读内容：

- [第十五章 构建赛博小镇](./chapter15/第十五章%20构建赛博小镇.md)
- [第十六章 毕业设计](./chapter16/第十六章%20毕业设计.md)
- [共创项目目录](../Co-creation-projects/README.md)

推荐项目：

构建一个“前端开发助手 Agent 平台”，支持需求拆解、组件方案、接口 mock、代码审查清单。

最小接口：

```text
POST /api/agent/run
GET /api/agent/runs/{id}
POST /api/tools/requirement-breakdown
POST /api/tools/component-suggestion
POST /api/tools/api-mock
POST /api/tools/code-review-checklist
```

最小能力：

- Vue 或 React 前端。
- FastAPI Agent 后端。
- 至少 3 个工具。
- 基础评估集。
- 任务状态、步骤日志、工具调用结果可视化。

第 12 周验收：

- 普通任务一次完成。
- 需要工具调用的任务能展示工具调用过程。
- 工具失败后有降级回复。
- 长输入场景下能做上下文裁剪或提示。
- Agent 输出不符合格式时，前端有兜底展示。

## 最终项目建议目录

```text
frontend-agent-assistant/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── models/
│   │   ├── services/
│   │   └── tools/
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── views/
│   └── package.json
└── evaluations/
    └── acceptance-cases.md
```

## 复盘问题

每周结束时回答以下问题：

- 本周最重要的 Agent 概念是什么？
- 哪段代码最值得反复阅读？
- 哪个错误最像真实工程问题？
- 如果把本周内容做成产品功能，用户会看到什么？
- 下周开始前需要补齐什么环境、密钥或知识？
