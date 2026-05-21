"""
本文件作用：封装一个通用的大语言模型 (LLM) 客户端，对接任何兼容 OpenAI 接口的服务，使用流式响应。

主要内容：
- HelloAgentsLLM：LLM 客户端类，负责初始化连接参数并调用模型进行对话

依赖说明：
- openai：OpenAI 官方 SDK，这里用它来调用兼容 OpenAI 格式的 API（不一定是 OpenAI 本身）
- dotenv：从 .env 文件加载环境变量，类似前端项目用 .env.local 配置密钥的方式
"""
import os
 # OpenAI 官方 SDK，类似前端用 axios 创建一个预配置的 HTTP 客户端
from openai import OpenAI
# 从 .env 文件读取环境变量，类似 Vite/CRA 里的 import.meta.env
from dotenv import load_dotenv
 # 类型注解，类似 TS 的 Array<T> 和 Record<string, string>
from typing import List, Dict

# 加载 .env 文件中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    为本书 "Hello Agents" 定制的LLM客户端。
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。

        参数：
            model (str): 模型 ID，如 "gpt-4" 或 "deepseek-chat"
            apiKey (str): API 密钥
            baseUrl (str): API 服务地址
            timeout (int): 超时秒数

        # 类似 JS 里创建 axios 实例时传 config：
        # const client = axios.create({ baseURL, headers: { Authorization }, timeout })
        """
        # or 运算符：如果左边是 None/空字符串就取右边。类似 JS 的 ?? (空值合并) 或 ||
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        # all() 检查列表里的元素是否全部为真值，类似 JS 的 [a, b, c].every(Boolean)
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        # 创建 OpenAI 客户端实例，后续通过它发请求
        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。

        参数：
            messages (List[Dict]): 对话消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature (float): 控制随机性，0 = 确定性输出，1 = 更随机

        返回：
            str: 模型的完整回复文本，失败返回 None
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,  # 流式响应：数据一块块到达，类似前端用 fetch + ReadableStream 或 EventSource (SSE)
            )

            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                # 遍历流式响应的每个片段（chunk），类似 JS 里：
                # for await (const chunk of response.body) { ... }
                if not chunk.choices:
                    continue
                # .delta.content 是这个片段新增的文本（增量），可能为 None
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)  # end="" 不换行，flush=True 立即输出（不缓冲）
                collected_content.append(content)
            print()  # 在流式输出结束后换行
            # "".join(list) 把列表里的字符串拼起来，类似 JS 的 arr.join("")
            return "".join(collected_content)

        except Exception as e:
            # 捕获所有异常，类似 JS 的 try { } catch(e) { }
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

# --- 客户端使用示例 ---
if __name__ == '__main__':
    # 仅在直接运行此文件时执行，被 import 时不执行
    # 类似 Node 里的 if (require.main === module) { ... }
    try:
        llmClient = HelloAgentsLLM()

        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]

        print("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        print(e)
