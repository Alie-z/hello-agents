"""
本文件作用：测试高级搜索工具，包括多源搜索、API 配置检查和与 Agent 的集成。

测试内容：
- test_advanced_search()：执行多个搜索查询
- test_api_configuration()：检查 API 配置是否正确
- test_with_agent()：展示工具描述（Agent 集成准备）
"""
# test_advanced_search.py
from dotenv import load_dotenv
from my_advanced_search import create_advanced_search_registry, MyAdvancedSearchTool

# 加载环境变量
load_dotenv()

def test_advanced_search():
    """测试高级搜索工具"""

    # 创建包含高级搜索工具的注册表
    registry = create_advanced_search_registry()

    print("🔍 测试高级搜索工具\n")

    # 测试查询
    test_queries = [
        "Python编程语言的历史",
        "人工智能的最新发展",
        "2024年科技趋势"
    ]

    # enumerate(list, 1) 从 1 开始编号
    for i, query in enumerate(test_queries, 1):
        print(f"测试 {i}: {query}")
        result = registry.execute_tool("advanced_search", query)
        print(f"结果: {result}\n")
        print("-" * 60 + "\n")

def test_api_configuration():
    """测试API配置检查"""
    print("🔧 测试API配置检查:")

    # 直接创建搜索工具实例
    # 构造时会自动检测哪些 API Key 可用
    search_tool = MyAdvancedSearchTool()

    # 如果没有配置API，会显示配置提示
    result = search_tool.search("机器学习算法")
    print(f"搜索结果: {result}")

def test_with_agent():
    """测试与Agent的集成"""
    print("\n🤖 与Agent集成测试:")
    print("高级搜索工具已准备就绪，可以与Agent集成使用")

    # 显示工具描述
    # Agent 在构建 prompt 时会调用这个方法，获取工具的文本描述
    registry = create_advanced_search_registry()
    tools_desc = registry.get_tools_description()
    print(f"工具描述:\n{tools_desc}")

if __name__ == "__main__":
    test_advanced_search()
    test_api_configuration()
    test_with_agent()
