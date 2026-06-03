"""
本文件作用：自定义 LLM 客户端，通过继承框架的 HelloAgentsLLM 来支持 ModelScope 服务。

主要内容：
- MyLLM：继承 HelloAgentsLLM，添加对 ModelScope provider 的支持

依赖说明：
- openai：OpenAI SDK，这里用来连接 ModelScope 兼容的 API 接口
- hello_agents：本项目的核心框架库，提供 HelloAgentsLLM 基类
"""
# my_llm.py
import os
# Optional 类型注解，表示"值可以是指定类型，也可以是 None"
# 类似 TS 的 string | null
from typing import Optional
# OpenAI SDK，用它来创建 HTTP 客户端调用兼容 OpenAI 格式的 API
from openai import OpenAI
# 从框架中导入 LLM 基类，我们的 MyLLM 将继承它
from hello_agents import HelloAgentsLLM

# 继承 HelloAgentsLLM，类似 JS 的 class MyLLM extends HelloAgentsLLM {}
class MyLLM(HelloAgentsLLM):
    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = "auto",
        # **kwargs 收集所有未声明的关键字参数到一个字典里
        # JS 没有直接对应，近似于把剩余命名参数收进一个 options 对象
        **kwargs
    ):
        # 检查provider是否为我们想处理的'modelscope'
        if provider == "modelscope":
            print("正在使用自定义的 ModelScope Provider")
            self.provider = "modelscope"
            
            # 解析 ModelScope 的凭证
            # or 运算符：左边为 None/空时取右边，类似 JS 的 ?? (空值合并)
            self.api_key = api_key or os.getenv("MODELSCOPE_API_KEY")
            self.base_url = base_url or "https://api-inference.modelscope.cn/v1/"
            
            # 验证凭证是否存在
            if not self.api_key:
                # raise 抛出异常，类似 JS 的 throw new Error(...)
                raise ValueError("ModelScope API key not found. Please set MODELSCOPE_API_KEY environment variable.")

            # 设置默认模型和其他参数
            self.model = model or os.getenv("LLM_MODEL_ID") or "Qwen/Qwen2.5-VL-72B-Instruct"
            # kwargs.get('key', default) 安全取值，取不到用默认值
            # 类似 JS 的 options.temperature ?? 0.7
            self.temperature = kwargs.get('temperature', 0.7)
            self.max_tokens = kwargs.get('max_tokens')
            self.timeout = kwargs.get('timeout', 60)
            
            # 使用获取的参数创建OpenAI客户端实例
            # _前缀表示"私有属性"（仅是约定，Python 不强制）
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)

        else:
            # 如果不是 modelscope, 则完全使用父类的原始逻辑来处理
            # super().__init__() 调用父类构造函数，类似 JS 的 super(...)
            super().__init__(model=model, api_key=api_key, base_url=base_url, provider=provider, **kwargs)
