"""
本文件作用：定义搜索工具和工具执行器，让 Agent 能够调用外部工具（如网页搜索）。

主要内容：
- search：基于 SerpApi 的网页搜索函数，查询 Google 并智能解析结果
- ToolExecutor：工具管理器类，负责注册、查找和列出可用工具

依赖说明：
- serpapi：Google 搜索 API 的 Python SDK，把 Google 搜索结果结构化返回
- dotenv：加载 .env 环境变量
"""
from dotenv import load_dotenv
# 加载 .env 文件中的环境变量
load_dotenv()

import os
from serpapi import SerpApiClient  # SerpApi SDK，用于调 Google 搜索接口，类似前端调第三方 REST API
from typing import Dict, Any  # 类型注解，Dict 类似 TS 的 Record<string, any>

def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。

    参数：
        query (str): 搜索关键词

    返回：
        str: 搜索结果的文本摘要

    # 类似前端里封装一个 searchGoogle 函数：
    # async function searchGoogle(query: string): Promise<string> { ... }
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误：SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn", # 语言代码
        }

        # 创建客户端并发请求，类似 JS：const res = await fetch(url, { params })
        client = SerpApiClient(params)
        results = client.get_dict()  # 返回 Python dict（字典），类似 JS 的 await res.json()

        # 智能解析：优先寻找最直接的答案
        # 按优先级依次检查不同类型的搜索结果
        if "answer_box_list" in results:
            # "\n".join(list) 把列表拼成换行分隔的字符串，类似 JS 的 arr.join("\n")
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            # ↑ 列表推导式 + enumerate，等价于 JS：
            # results.organic_results.slice(0, 3).map((res, i) =>
            #   `[${i+1}] ${res.title ?? ''}\n${res.snippet ?? ''}`
            # )
            return "\n\n".join(snippets)

        # f-string 类似 JS 模板字符串 `对不起，没有找到关于 '${query}' 的信息。`
        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"

from typing import Dict, Any

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。

    # 类似前端里的插件注册中心：
    # class PluginRegistry {
    #   plugins = new Map();
    #   register(name, plugin) { this.plugins.set(name, plugin); }
    #   get(name) { return this.plugins.get(name); }
    # }
    """
    def __init__(self):
        # self 是当前实例，类似 JS class 方法里的 this
        # Dict[str, Dict[str, Any]] 类似 TS 的 Record<string, { description: string; func: Function }>
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具。

        参数：
            name (str): 工具名称
            description (str): 工具的功能描述（会被送入 LLM prompt，让模型知道什么时候该用它）
            func (callable): 实际执行的函数，callable 类似 TS 的 (...args: any[]) => any
        """
        if name in self.tools:
            print(f"警告：工具 '{name}' 已存在，将被覆盖。")

        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。

        参数：
            name (str): 工具名称

        返回：
            callable: 工具函数，如果找不到返回 None
        """
        # .get(name, {}) 安全取值，key 不存在时返回空 dict 而不是报错
        # 类似 JS 的 (this.tools[name] ?? {}).func
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。

        返回：
            str: 每行一个工具，格式为 "- 工具名: 描述"
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
            # .items() 遍历字典的 key-value 对，类似 JS 的 Object.entries(this.tools)
            # 列表推导式，等价于 JS：
            # Object.entries(this.tools).map(([name, info]) => `- ${name}: ${info.description}`)
        ])


# --- 工具初始化与使用示例 ---
if __name__ == '__main__':
    # 仅在直接运行此文件时执行，被 import 时跳过
    # 类似 Node 里的 if (require.main === module) { ... }

    # 1. 初始化工具执行器
    toolExecutor = ToolExecutor()

    # 2. 注册我们的实战搜索工具
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    toolExecutor.registerTool("Search", search_description, search)

    # 3. 打印可用的工具
    print("\n--- 可用的工具 ---")
    print(toolExecutor.getAvailableTools())

    # 4. 智能体的Action调用，这次我们问一个实时性的问题
    print("\n--- 执行 Action: Search['英伟达最新的GPU型号是什么'] ---")
    tool_name = "Search"
    tool_input = "英伟达最新的GPU型号是什么"

    tool_function = toolExecutor.getTool(tool_name)
    if tool_function:
        observation = tool_function(tool_input)
        print("--- 观察 (Observation) ---")
        print(observation)
    else:
        print(f"错误：未找到名为 '{tool_name}' 的工具。")
