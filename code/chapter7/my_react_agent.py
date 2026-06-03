"""
本文件作用：自定义 ReAct Agent（推理+行动智能体），实现 Thought → Action → Observation 循环。

主要内容：
- MY_REACT_PROMPT：ReAct 模式的提示词模板
- MyReActAgent：继承框架 ReActAgent，实现自定义的推理行动循环

依赖说明：
- hello_agents：框架提供 ReActAgent 基类、HelloAgentsLLM、ToolRegistry 等
- re：正则表达式，用于解析 LLM 输出中的 Thought/Action
"""
# 提示词模板：定义了 LLM 的工作格式（Thought + Action）
# {tools}、{question}、{history} 是占位符，后面用 .format() 填充
# 双花括号 {{ }} 是转义，输出时变成单花括号 { }（类似 JS 模板字符串里的转义）
MY_REACT_PROMPT = """你是一个具备推理和行动能力的AI助手。你可以通过思考分析问题，然后调用合适的工具来获取信息，最终给出准确的答案。

## 可用工具
{tools}

## 工作流程
请严格按照以下格式进行回应，每次只能执行一个步骤：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，必须是以下格式之一：
- `{{tool_name}}[{{tool_input}}]` - 调用指定工具
- `Finish[最终答案]` - 当你有足够信息给出最终答案时

## 重要提醒
1. 每次回应必须包含Thought和Action两部分
2. 工具调用的格式必须严格遵循：工具名[参数]
3. 只有当你确信有足够信息回答问题时，才使用Finish
4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数

## 当前任务
**Question:** {question}

## 执行历史
{history}

现在开始你的推理和行动：
"""

import re
# Tuple 类型注解，表示固定长度和类型的元组，类似 TS 的 [string, string]
from typing import Optional, List, Tuple
from hello_agents import ReActAgent, HelloAgentsLLM, Config, Message, ToolRegistry

# 继承 ReActAgent，类似 JS 的 class MyReActAgent extends ReActAgent {}
class MyReActAgent(ReActAgent):
    """
    重写的ReAct Agent - 推理与行动结合的智能体
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        tool_registry: ToolRegistry,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
        custom_prompt: Optional[str] = None
    ):
        # 调用父类构造函数
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        self.max_steps = max_steps
        # List[str] 类型注解，类似 TS 的 string[]
        self.current_history: List[str] = []
        # if...else 三元表达式：有自定义 prompt 就用自定义的，否则用默认的
        self.prompt_template = custom_prompt if custom_prompt else MY_REACT_PROMPT
        print(f"✅ {name} 初始化完成，最大步数: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        """
        运行ReAct Agent：循环执行 思考→行动→观察 直到得出答案。

        参数：
            input_text (str): 用户的问题
            **kwargs: 传给 LLM 的额外参数

        返回：
            str: 最终答案
        """
        self.current_history = []
        current_step = 0

        print(f"\n🤖 {self.name} 开始处理问题: {input_text}")

        # while 循环驱动 ReAct 的核心流程
        while current_step < self.max_steps:
            current_step += 1
            print(f"\n--- 第 {current_step} 步 ---")

            # 1. 构建提示词：把工具描述、问题、历史填入模板
            tools_desc = self.tool_registry.get_tools_description()
            # "\n".join(list) 把列表拼成换行分隔的字符串
            # 类似 JS 的 array.join("\n")
            history_str = "\n".join(self.current_history)
            prompt = self.prompt_template.format(
                tools=tools_desc,
                question=input_text,
                history=history_str
            )

            # 2. 调用LLM
            messages = [{"role": "user", "content": prompt}]
            response_text = self.llm.invoke(messages, **kwargs)

            # 3. 解析输出：从 LLM 响应中提取 Thought 和 Action
            thought, action = self._parse_output(response_text)

            # 4. 检查完成条件
            if action and action.startswith("Finish"):
                # 提取 Finish[xxx] 中的最终答案
                final_answer = self._parse_action_input(action)
                self.add_message(Message(input_text, "user"))
                self.add_message(Message(final_answer, "assistant"))
                return final_answer

            # 5. 执行工具调用
            if action:
                # 解析 "工具名[参数]" 格式
                tool_name, tool_input = self._parse_action(action)
                # 通过工具注册表执行对应的工具函数
                observation = self.tool_registry.execute_tool(tool_name, tool_input)
                # 把本步的行动和观察追加到历史，下一轮 LLM 可以看到
                self.current_history.append(f"Action: {action}")
                self.current_history.append(f"Observation: {observation}")

        # 达到最大步数
        final_answer = "抱歉，我无法在限定步数内完成这个任务。"
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer
