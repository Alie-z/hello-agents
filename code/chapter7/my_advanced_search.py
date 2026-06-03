"""
本文件作用：自定义高级搜索工具，整合多个搜索源（Tavily、SerpApi），自动选择最佳结果。

主要内容：
- MyAdvancedSearchTool：多源智能搜索工具类，自动检测可用 API 并降级
- create_advanced_search_registry：创建包含高级搜索的工具注册表

依赖说明：
- tavily：Tavily AI 搜索 API 客户端（可选，需配置 TAVILY_API_KEY）
- serpapi：Google 搜索 API 客户端（可选，需配置 SERPAPI_API_KEY）
- hello_agents：框架提供 ToolRegistry 工具注册表
"""
# my_advanced_search.py
import os
# Any 表示任意类型，类似 TS 的 any
from typing import Optional, List, Dict, Any
from hello_agents import ToolRegistry

class MyAdvancedSearchTool:
    """
    自定义高级搜索工具类
    展示多源整合和智能选择的设计模式

    设计思路类似前端的"多 CDN 降级"：先尝试首选源，失败了切到备选源。
    """

    def __init__(self):
        self.name = "my_advanced_search"
        self.description = "智能搜索工具，支持多个搜索源，自动选择最佳结果"
        self.search_sources = []
        self._setup_search_sources()

    def _setup_search_sources(self):
        """
        设置可用的搜索源。
        检查环境变量中是否配置了各搜索服务的 API Key，有就启用。
        """
        # 检查Tavily可用性
        if os.getenv("TAVILY_API_KEY"):
            try:
                # 条件导入：只在需要时才导入第三方包
                # 类似 JS 的动态 import()：const { TavilyClient } = await import('tavily')
                from tavily import TavilyClient
                self.tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
                self.search_sources.append("tavily")
                print("✅ Tavily搜索源已启用")
            except ImportError:
                # ImportError：包没安装时抛出
                # 类似 JS 的 import() 找不到模块时的 error
                print("⚠️ Tavily库未安装")

        # 检查SerpApi可用性
        if os.getenv("SERPAPI_API_KEY"):
            try:
                import serpapi
                self.search_sources.append("serpapi")
                print("✅ SerpApi搜索源已启用")
            except ImportError:
                print("⚠️ SerpApi库未安装")

        if self.search_sources:
            # ', '.join(list) 把列表用逗号拼成字符串
            # 类似 JS 的 array.join(', ')
            print(f"🔧 可用搜索源: {', '.join(self.search_sources)}")
        else:
            print("⚠️ 没有可用的搜索源，请配置API密钥")

    def search(self, query: str) -> str:
        """
        执行智能搜索：按优先级尝试各搜索源，返回第一个成功的结果。

        参数：
            query (str): 搜索关键词

        返回：
            str: 格式化的搜索结果
        """
        if not query.strip():
            return "❌ 错误：搜索查询不能为空"

        # 检查是否有可用的搜索源
        if not self.search_sources:
            return """❌ 没有可用的搜索源，请配置以下API密钥之一：

1. Tavily API: 设置环境变量 TAVILY_API_KEY
   获取地址: https://tavily.com/

2. SerpAPI: 设置环境变量 SERPAPI_API_KEY
   获取地址: https://serpapi.com/

配置后重新运行程序。"""

        print(f"🔍 开始智能搜索: {query}")

        # 尝试多个搜索源，返回最佳结果
        # 降级策略：第一个失败就试下一个，类似前端的多 CDN fallback
        for source in self.search_sources:
            try:
                if source == "tavily":
                    result = self._search_with_tavily(query)
                    # "not in" 检查子串不存在，类似 JS 的 !result.includes("未找到")
                    if result and "未找到" not in result:
                        return f"📊 Tavily AI搜索结果：\n\n{result}"

                elif source == "serpapi":
                    result = self._search_with_serpapi(query)
                    if result and "未找到" not in result:
                        return f"🌐 SerpApi Google搜索结果：\n\n{result}"

            except Exception as e:
                print(f"⚠️ {source} 搜索失败: {e}")
                # continue 跳过当前迭代，试下一个源
                continue

        return "❌ 所有搜索源都失败了，请检查网络连接和API密钥配置"

    def _search_with_tavily(self, query: str) -> str:
        """
        使用Tavily搜索。

        参数：
            query (str): 搜索词

        返回：
            str: 格式化的搜索结果
        """
        response = self.tavily_client.search(query=query, max_results=3)

        # .get('key') 安全取值，key 不存在返回 None 而不报错
        # 类似 JS 的 response?.answer
        if response.get('answer'):
            result = f"💡 AI直接答案：{response['answer']}\n\n"
        else:
            result = ""

        result += "🔗 相关结果：\n"
        # enumerate(list, 1) 从 1 开始编号遍历
        # 类似 JS 的 list.forEach((item, index) => { const i = index + 1; ... })
        for i, item in enumerate(response.get('results', [])[:3], 1):
            result += f"[{i}] {item.get('title', '')}\n"
            # [:150] 切片取前 150 个字符，类似 JS 的 str.slice(0, 150)
            result += f"    {item.get('content', '')[:150]}...\n\n"

        return result

    def _search_with_serpapi(self, query: str) -> str:
        """
        使用SerpApi搜索。

        参数：
            query (str): 搜索词

        返回：
            str: 格式化的搜索结果
        """
        import serpapi

        search = serpapi.GoogleSearch({
            "q": query,
            "api_key": os.getenv("SERPAPI_API_KEY"),
            "num": 3
        })

        # .get_dict() 发请求并返回结果字典
        # 类似 JS 的 await fetch(url).then(r => r.json())
        results = search.get_dict()

        result = "🔗 Google搜索结果：\n"
        # "in" 检查 key 是否存在于字典中
        # 类似 JS 的 "organic_results" in results 或 results.hasOwnProperty(...)
        if "organic_results" in results:
            for i, res in enumerate(results["organic_results"][:3], 1):
                result += f"[{i}] {res.get('title', '')}\n"
                result += f"    {res.get('snippet', '')}\n\n"

        return result

def create_advanced_search_registry():
    """
    创建包含高级搜索工具的注册表。

    返回：
        ToolRegistry: 注册了 advanced_search 工具的注册表
    """
    registry = ToolRegistry()

    # 创建搜索工具实例
    search_tool = MyAdvancedSearchTool()

    # 注册搜索工具的方法作为函数
    # 把实例方法注册为工具：Agent 调用 "advanced_search" 时会执行 search_tool.search()
    registry.register_function(
        name="advanced_search",
        description="高级搜索工具，整合Tavily和SerpAPI多个搜索源，提供更全面的搜索结果",
        func=search_tool.search
    )

    return registry
