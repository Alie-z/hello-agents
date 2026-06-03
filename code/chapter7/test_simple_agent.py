"""
本文件作用：测试 MySimpleAgent 的各项功能，包括基础对话、工具调用、流式响应、动态工具管理。

测试内容：
- 测试1：无工具的纯对话
- 测试2：带工具（计算器）的对话
- 测试3：流式响应输出
- 测试4：动态添加/管理工具
"""
# test_simple_agent.py
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM, ToolRegistry
# CalculatorTool 是框架内置的计算器工具类
from hello_agents.tools import CalculatorTool
from my_simple_agent import MySimpleAgent

# 加载环境变量
load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM()

# 测试1：基础对话Agent（无工具）
print("=== 测试1：基础对话 ===")
basic_agent = MySimpleAgent(
    name="基础助手",
    llm=llm,
    system_prompt="你是一个友好的AI助手，请用简洁明了的方式回答问题。"
)

response1 = basic_agent.run("你好，请介绍一下自己")
print(f"基础对话响应: {response1}\n")

# 测试2：带工具的Agent
print("=== 测试2：工具增强对话 ===")
# ToolRegistry 是工具注册表，管理所有可用工具
# 类似前端的"插件注册中心"
tool_registry = ToolRegistry()
calculator = CalculatorTool()
# register_tool 注册工具实例到注册表
tool_registry.register_tool(calculator)

enhanced_agent = MySimpleAgent(
    name="增强助手",
    llm=llm,
    system_prompt="你是一个智能助手，可以使用工具来帮助用户。",
    tool_registry=tool_registry,
    enable_tool_calling=True
)

response2 = enhanced_agent.run("请帮我计算 15 * 8 + 32")
print(f"工具增强响应: {response2}\n")

# 测试3：流式响应
print("=== 测试3：流式响应 ===")
print("流式响应: ", end="")
# stream_run 返回生成器，for...in 逐块消费
# 类似 JS 的 for await (const chunk of agent.streamRun(...))
for chunk in basic_agent.stream_run("请解释什么是人工智能"):
    # 内容已在stream_run中实时打印
    pass

# 测试4：动态添加工具
print("\n=== 测试4：动态工具管理 ===")
print(f"添加工具前: {basic_agent.has_tools()}")
basic_agent.add_tool(calculator)
print(f"添加工具后: {basic_agent.has_tools()}")
print(f"可用工具: {basic_agent.list_tools()}")

# 查看对话历史
# .get_history() 是父类方法，返回所有历史消息
print(f"\n对话历史: {len(basic_agent.get_history())} 条消息")
