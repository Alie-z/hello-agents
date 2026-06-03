"""
本文件作用：测试自定义计算器工具，包括基本运算和与 Agent 的集成。

测试内容：
- test_calculator_tool()：独立测试计算器（加减乘除、sqrt）
- test_with_simple_agent()：测试计算器与 SimpleAgent 的配合
"""
# test_my_calculator.py
from dotenv import load_dotenv
from my_calculator_tool import create_calculator_registry

# 加载环境变量
load_dotenv()

def test_calculator_tool():
    """测试自定义计算器工具"""

    # 创建包含计算器的注册表
    registry = create_calculator_registry()

    print("🧪 测试自定义计算器工具\n")

    # 简单测试用例
    test_cases = [
        "2 + 3",           # 基本加法
        "10 - 4",          # 基本减法
        "5 * 6",           # 基本乘法
        "15 / 3",          # 基本除法
        "sqrt(16)",        # 平方根
    ]

    # enumerate(list, 1) 从 1 开始编号遍历
    # 类似 JS 的 testCases.forEach((expr, index) => { const i = index + 1; ... })
    for i, expression in enumerate(test_cases, 1):
        print(f"测试 {i}: {expression}")
        # execute_tool 通过工具名调用对应的函数
        result = registry.execute_tool("my_calculator", expression)
        print(f"结果: {result}\n")

def test_with_simple_agent():
    """测试与SimpleAgent的集成"""
    from hello_agents import HelloAgentsLLM

    # 创建LLM客户端
    llm = HelloAgentsLLM()

    # 创建包含计算器的注册表
    registry = create_calculator_registry()

    print("🤖 与SimpleAgent集成测试:")

    # 模拟SimpleAgent使用工具的场景
    user_question = "请帮我计算 sqrt(16) + 2 * 3"

    print(f"用户问题: {user_question}")

    # 使用工具计算
    calc_result = registry.execute_tool("my_calculator", "sqrt(16) + 2 * 3")
    print(f"计算结果: {calc_result}")

    # 构建最终回答：把计算结果交给 LLM 用自然语言回答
    final_messages = [
        {"role": "user", "content": f"计算结果是 {calc_result}，请用自然语言回答用户的问题：{user_question}"}
    ]

    print("\n🎯 SimpleAgent的回答:")
    # think() 返回流式响应（生成器）
    response = llm.think(final_messages)
    for chunk in response:
        print(chunk, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    test_calculator_tool()
    test_with_simple_agent()
