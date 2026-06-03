"""
本文件作用：自定义 SimpleAgent（简单对话智能体），支持可选的工具调用功能。

主要内容：
- MySimpleAgent：继承框架的 SimpleAgent，增加了工具调用能力
  - run()：普通对话 or 带工具调用的对话
  - stream_run()：流式输出版本
  - 工具管理方法：add_tool / remove_tool / list_tools

依赖说明：
- hello_agents：本项目核心框架，提供 SimpleAgent 基类、Config、Message 等
- re：Python 标准库，正则表达式，用于解析 LLM 输出中的工具调用指令
"""
# my_simple_agent.py
# Iterator 是迭代器类型注解，类似 TS 的 Iterable<string>
from typing import Optional, Iterator
# 从框架导入基类和相关类型
from hello_agents import SimpleAgent, HelloAgentsLLM, Config, Message
import re

# 继承 SimpleAgent 基类，类似 JS 的 class MySimpleAgent extends SimpleAgent {}
class MySimpleAgent(SimpleAgent):
    """
    重写的简单对话Agent
    展示如何基于框架基类构建自定义Agent
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        # Optional['ToolRegistry'] 用引号包裹是因为 ToolRegistry 可能还没被导入（前向引用）
        # 类似 TS 里写类型时引用还没声明的接口
        tool_registry: Optional['ToolRegistry'] = None,
        enable_tool_calling: bool = True
    ):
        # 调用父类构造函数，类似 JS 的 super(name, llm, systemPrompt, config)
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        # and 短路运算：两个条件都为真才为 True
        # 类似 JS 的 enableToolCalling && toolRegistry !== null
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
        # 三元表达式：x if condition else y，类似 JS 的 condition ? x : y
        print(f"✅ {name} 初始化完成，工具调用: {'启用' if self.enable_tool_calling else '禁用'}")

    def run(self, input_text: str, max_tool_iterations: int = 3, **kwargs) -> str:
        """
        重写的运行方法 - 实现简单对话逻辑，支持可选工具调用

        参数：
            input_text (str): 用户输入的文本
            max_tool_iterations (int): 工具调用最大循环次数，防止无限调用
            **kwargs: 传给 LLM 的额外参数

        返回：
            str: Agent 的最终回复
        """
        print(f"🤖 {self.name} 正在处理: {input_text}")

        # 构建消息列表
        messages = []

        # 添加系统消息（可能包含工具信息）
        enhanced_system_prompt = self._get_enhanced_system_prompt()
        messages.append({"role": "system", "content": enhanced_system_prompt})

        # 添加历史消息
        # self._history 是父类维护的对话历史列表
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        # 添加当前用户消息
        messages.append({"role": "user", "content": input_text})

        # 如果没有启用工具调用，使用简单对话逻辑
        if not self.enable_tool_calling:
            # .invoke() 一次性调用 LLM 并返回完整响应，.content 取文本内容
            response = self.llm.invoke(messages, **kwargs).content
            # Message 是框架定义的消息对象，存入对话历史
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(response, "assistant"))
            print(f"✅ {self.name} 响应完成")
            return response

        # 支持多轮工具调用的逻辑
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)

    def _get_enhanced_system_prompt(self) -> str:
        """
        构建增强的系统提示词，包含工具信息。

        返回：
            str: 拼接了工具说明的 system prompt
        """
        # or 运算符：如果 self.system_prompt 为 None 就用默认值
        base_prompt = self.system_prompt or "你是一个有用的AI助手。"

        if not self.enable_tool_calling or not self.tool_registry:
            return base_prompt

        # 获取工具描述
        tools_description = self.tool_registry.get_tools_description()
        if not tools_description or tools_description == "暂无可用工具":
            return base_prompt

        # 拼接工具说明到 system prompt 末尾
        # 告诉 LLM 它有哪些工具可用，以及怎么格式化工具调用
        tools_section = "\n\n## 可用工具\n"
        tools_section += "你可以使用以下工具来帮助回答问题：\n"
        tools_section += tools_description + "\n"

        tools_section += "\n## 工具调用格式\n"
        tools_section += "当需要使用工具时，请使用以下格式：\n"
        tools_section += "`[TOOL_CALL:{tool_name}:{parameters}]`\n"
        tools_section += "例如：`[TOOL_CALL:search:Python编程]` 或 `[TOOL_CALL:memory:recall=用户信息]`\n\n"
        tools_section += "工具调用结果会自动插入到对话中，然后你可以基于结果继续回答。\n"

        return base_prompt + tools_section

    def _run_with_tools(self, messages: list, input_text: str, max_tool_iterations: int, **kwargs) -> str:
        """
        支持工具调用的运行逻辑：循环调用 LLM，如果返回中包含工具调用指令，就执行工具并继续。

        参数：
            messages (list): 当前对话消息列表
            input_text (str): 用户原始输入
            max_tool_iterations (int): 最大循环次数
            **kwargs: 传给 LLM 的额外参数

        返回：
            str: 最终回复（不含工具调用标记）
        """
        current_iteration = 0
        final_response = ""

        # while 循环，类似 JS 的 while (currentIteration < maxToolIterations)
        while current_iteration < max_tool_iterations:
            # 调用LLM
            response = self.llm.invoke(messages, **kwargs).content

            # 检查是否有工具调用
            # 从 LLM 返回的文本中解析出 [TOOL_CALL:xxx:yyy] 格式的指令
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                print(f"🔧 检测到 {len(tool_calls)} 个工具调用")
                # 执行所有工具调用并收集结果
                tool_results = []
                clean_response = response

                for call in tool_calls:
                    result = self._execute_tool_call(call['tool_name'], call['parameters'])
                    tool_results.append(result)
                    # 从响应中移除工具调用标记
                    # .replace() 替换字符串，类似 JS 的 str.replace(old, new)
                    clean_response = clean_response.replace(call['original'], "")

                # 构建包含工具结果的消息
                messages.append({"role": "assistant", "content": clean_response})

                # 添加工具结果，让 LLM 在下一轮基于结果回答
                tool_results_text = "\n\n".join(tool_results)
                messages.append({"role": "user", "content": f"工具执行结果：\n{tool_results_text}\n\n请基于这些结果给出完整的回答。"})

                current_iteration += 1
                # continue 跳过本次循环剩余部分，直接进入下一轮
                # 类似 JS 的 continue
                continue

            # 没有工具调用，这是最终回答
            final_response = response
            break

        # 如果超过最大迭代次数，获取最后一次回答
        if current_iteration >= max_tool_iterations and not final_response:
            final_response = self.llm.invoke(messages, **kwargs).content

        # 保存到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_response, "assistant"))
        print(f"✅ {self.name} 响应完成")

        return final_response

    def _parse_tool_calls(self, text: str) -> list:
        """
        解析文本中的工具调用指令。

        从 LLM 响应中匹配 [TOOL_CALL:工具名:参数] 格式的字符串。

        参数：
            text (str): LLM 的响应文本

        返回：
            list: 解析出的工具调用列表，每项包含 tool_name、parameters、original
        """
        # 正则表达式匹配 [TOOL_CALL:xxx:yyy] 格式
        # 类似 JS 的 /\[TOOL_CALL:([^:]+):([^\]]+)\]/g
        pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
        # re.findall 返回所有匹配的捕获组列表
        # 类似 JS 的 [...text.matchAll(pattern)]
        matches = re.findall(pattern, text)

        tool_calls = []
        # 解构赋值遍历，类似 JS 的 for (const [toolName, parameters] of matches)
        for tool_name, parameters in matches:
            tool_calls.append({
                'tool_name': tool_name.strip(),
                'parameters': parameters.strip(),
                'original': f'[TOOL_CALL:{tool_name}:{parameters}]'
            })

        return tool_calls

    def _execute_tool_call(self, tool_name: str, parameters: str) -> str:
        """
        执行工具调用。

        参数：
            tool_name (str): 工具名称
            parameters (str): 传给工具的参数字符串

        返回：
            str: 工具执行结果的格式化文本
        """
        if not self.tool_registry:
            return f"❌ 错误：未配置工具注册表"

        try:
            # 智能参数解析
            if tool_name == 'calculator':
                # 计算器工具直接传入表达式
                result = self.tool_registry.execute_tool(tool_name, parameters)
            else:
                # 其他工具使用智能参数解析
                param_dict = self._parse_tool_parameters(tool_name, parameters)
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    return f"❌ 错误：未找到工具 '{tool_name}'"
                result = tool.run(param_dict)

            return f"🔧 工具 {tool_name} 执行结果：\n{result}"

        except Exception as e:
            # 捕获所有异常，类似 JS 的 catch(e)
            # str(e) 把异常转成字符串，类似 JS 的 e.message
            return f"❌ 工具调用失败：{str(e)}"

    def _parse_tool_parameters(self, tool_name: str, parameters: str) -> dict:
        """
        智能解析工具参数字符串为字典。

        支持多种格式：
        - "key=value"（单参数）
        - "key1=val1,key2=val2"（多参数）
        - "直接文本"（根据工具类型推断参数名）

        参数：
            tool_name (str): 工具名称
            parameters (str): 原始参数字符串

        返回：
            dict: 解析后的参数字典，类似 JS 的 { key: value }
        """
        param_dict = {}

        if '=' in parameters:
            # 格式: key=value 或 action=search,query=Python
            if ',' in parameters:
                # 多个参数：action=search,query=Python,limit=3
                pairs = parameters.split(',')
                for pair in pairs:
                    if '=' in pair:
                        # .split('=', 1) 只分割第一个 =，避免值中有 = 被误切
                        # 类似 JS 的 pair.split('=') 但限制次数
                        key, value = pair.split('=', 1)
                        # .strip() 去除首尾空白，类似 JS 的 .trim()
                        param_dict[key.strip()] = value.strip()
            else:
                # 单个参数：key=value
                key, value = parameters.split('=', 1)
                param_dict[key.strip()] = value.strip()
        else:
            # 直接传入参数，根据工具类型智能推断参数名
            if tool_name == 'search':
                param_dict = {'query': parameters}
            elif tool_name == 'memory':
                param_dict = {'action': 'search', 'query': parameters}
            else:
                param_dict = {'input': parameters}

        return param_dict

    def stream_run(self, input_text: str, **kwargs) -> Iterator[str]:
        """
        自定义的流式运行方法。逐块产出 LLM 的响应文本。

        参数：
            input_text (str): 用户输入

        返回：
            Iterator[str]: 文本片段的迭代器（生成器）
            类似 JS 的 async function*，调用方用 for...of 消费

        # yield 让这个函数变成生成器（generator function）
        # 类似 JS 的 function* streamRun() { yield chunk; }
        """
        print(f"🌊 {self.name} 开始流式处理: {input_text}")

        messages = []

        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})

        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": input_text})

        # 流式调用LLM
        full_response = ""
        print("📝 实时响应: ", end="")
        for chunk in self.llm.stream_invoke(messages, **kwargs):
            full_response += chunk
            # flush=True 立即输出不缓冲，end="" 不换行
            print(chunk, end="", flush=True)
            # yield 暂停函数并产出一个值给调用方
            # 类似 JS generator 的 yield，调用方每次 next() 拿到一个 chunk
            yield chunk

        # 换行
        print()

        # 保存完整对话到历史记录
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(full_response, "assistant"))
        print(f"✅ {self.name} 流式响应完成")

    def add_tool(self, tool) -> None:
        """
        添加工具到Agent（便利方法）。

        参数：
            tool: 工具实例（需要有 name 属性）
        """
        if not self.tool_registry:
            # 延迟导入：只在需要时才导入，避免循环依赖
            # 类似 JS 的动态 import()
            from hello_agents import ToolRegistry
            self.tool_registry = ToolRegistry()
            self.enable_tool_calling = True

        self.tool_registry.register_tool(tool)
        print(f"🔧 工具 '{tool.name}' 已添加")

    def has_tools(self) -> bool:
        """检查是否有可用工具"""
        return self.enable_tool_calling and self.tool_registry is not None

    def remove_tool(self, tool_name: str) -> bool:
        """移除工具（便利方法）"""
        if self.tool_registry:
            self.tool_registry.unregister(tool_name)
            return True
        return False

    def list_tools(self) -> list:
        """列出所有可用工具"""
        if self.tool_registry:
            return self.tool_registry.list_tools()
        return []
