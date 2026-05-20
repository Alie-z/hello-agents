"""
本文件作用：实现 ReAct（Reasoning + Acting）模式的智能体。
ReAct 是一种让 LLM "边想边做"的模式：每一步先思考（Thought），再行动（Action），观察结果后继续循环，
直到得到最终答案。

主要内容：
- REACT_PROMPT_TEMPLATE：ReAct 的提示词模板，规定了 LLM 的输出格式
- ReActAgent：ReAct 智能体类，驱动"思考→行动→观察"循环

依赖说明：
- re：Python 标准库，正则表达式，类似 JS 的 RegExp
- llm_client：本项目的 LLM 客户端封装
- tools：本项目的工具注册/执行器
"""
import re  # 正则表达式库，用法和 JS 的 RegExp 类似，但语法是函数式的：re.search(pattern, text)
from llm_client import HelloAgentsLLM
from tools import ToolExecutor, search

# (此处省略 REACT_PROMPT_TEMPLATE 的定义)
# 下面是 ReAct 的核心提示词模板
# 模板里的 {tools}、{question}、{history} 是占位符，后面用 .format() 替换
# 类似 JS 模板字符串里的 ${变量}，但这里是延迟填充的
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下：
{tools}

请严格按照以下格式进行回应：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]`：调用一个可用工具。
- `Finish[最终答案]`：当你认为已经获得最终答案时。
- 当你收集到足够的信息，能够回答用户的最终问题时，你必须在`Action:`字段后使用 `Finish[最终答案]` 来输出最终答案。


现在，请开始解决以下问题：
Question: {question}
History: {history}
"""

class ReActAgent:
    """
    ReAct 智能体：实现 Thought → Action → Observation 循环。

    工作流程类似前端里的状态机或 Redux middleware：
    1. 接收输入 → 2. 调用 LLM 得到思考+行动 → 3. 执行行动得到观察 → 4. 把观察追加到历史 → 回到 2
    循环直到 LLM 发出 Finish 或达到最大步数。
    """
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_steps: int = 5):
        """
        参数：
            llm_client: LLM 客户端实例
            tool_executor: 工具执行器，里面注册了可用的工具
            max_steps (int): 最大循环步数，防止无限循环
        """
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_steps = max_steps
        self.history = []  # 存储历史行动和观察，类似 JS 的 const history: string[] = []

    def run(self, question: str):
        """
        运行 ReAct 智能体，处理用户问题。

        参数：
            question (str): 用户提出的问题

        返回：
            str | None: 最终答案，达到最大步数时返回 None
        """
        self.history = []
        current_step = 0

        # while 循环，类似 JS 的 while (currentStep < this.maxSteps) { ... }
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            # 构造 prompt：把工具描述、问题、历史填入模板
            tools_desc = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)  # 列表拼字符串，类似 JS 的 this.history.join("\n")
            prompt = REACT_PROMPT_TEMPLATE.format(tools=tools_desc, question=question, history=history_str)

            # 调用 LLM 获取思考和行动
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误：LLM未能返回有效响应。"); break

            # 解析 LLM 输出，提取 Thought 和 Action
            thought, action = self._parse_output(response_text)
            if thought: print(f"🤔 思考: {thought}")
            if not action: print("警告：未能解析出有效的Action，流程终止。"); break

            # 检查是否是结束指令
            if action.startswith("Finish"):
                # 如果是Finish指令，提取最终答案并结束
                final_answer = self._parse_action_input(action)
                print(f"🎉 最终答案: {final_answer}")
                return final_answer

            # 解析工具调用：从 "Search[xxx]" 中提取工具名和输入
            tool_name, tool_input = self._parse_action(action)
            if not tool_name or not tool_input:
                self.history.append("Observation: 无效的Action格式，请检查。"); continue

            # 执行工具调用
            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)
            # 条件表达式，类似 JS 三元：toolFunction ? toolFunction(input) : "错误..."
            observation = tool_function(tool_input) if tool_function else f"错误：未找到名为 '{tool_name}' 的工具。"

            # 将行动和观察追加到历史中，下一轮 LLM 可以看到之前发生了什么
            print(f"👀 观察: {observation}")
            self.history.append(f"Action: {action}")
            self.history.append(f"Observation: {observation}")

        print("已达到最大步数，流程终止。")
        return None

    def _parse_output(self, text: str):
        """
        从 LLM 的输出文本中解析出 Thought 和 Action。

        使用正则表达式匹配，类似 JS 的：
        const thoughtMatch = text.match(/Thought:\s*(.*?)(?=\nAction:|$)/s)
        """
        # re.DOTALL 让 . 能匹配换行符，类似 JS 正则的 /s 标志
        thought_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|$)", text, re.DOTALL)
        # Action: 匹配到文本末尾
        action_match = re.search(r"Action:\s*(.*?)$", text, re.DOTALL)
        # .group(1) 取第一个捕获组，类似 JS 的 match[1]
        thought = thought_match.group(1).strip() if thought_match else None
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action_text: str):
        """
        解析 "ToolName[input]" 格式，返回 (工具名, 输入)。

        类似 JS：const [, name, input] = action.match(/(\w+)\[(.*)\]/s) || []
        """
        match = re.match(r"(\w+)\[(.*)\]", action_text, re.DOTALL)
        # 元组解包返回，类似 JS 返回数组 [match[1], match[2]]
        return (match.group(1), match.group(2)) if match else (None, None)

    def _parse_action_input(self, action_text: str):
        """从 "Finish[xxx]" 中提取 xxx 部分。"""
        match = re.match(r"\w+\[(.*)\]", action_text, re.DOTALL)
        return match.group(1) if match else ""

# --- 主程序入口 ---
if __name__ == '__main__':
    # 仅在直接运行此文件时执行
    # 类似 Node 里的 if (require.main === module) { ... }
    llm = HelloAgentsLLM()
    tool_executor = ToolExecutor()
    search_desc = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_desc, search)
    agent = ReActAgent(llm_client=llm, tool_executor=tool_executor)
    question = "华为最新的手机是哪一款？它的主要卖点是什么？"
    agent.run(question)
