"""
本文件作用：程序入口，演示如何实例化自定义 LLM 客户端并调用模型。

主要内容：
- 创建 MyLLM 实例（自定义的 ModelScope provider）
- 调用 think 方法进行对话

依赖说明：
- dotenv：从 .env 文件加载环境变量，类似前端项目 .env.local 的作用
- my_llm：本目录下的自定义 LLM 客户端模块
"""
# my_main.py
from dotenv import load_dotenv
# 注意：这里导入我们自己的类（继承自框架的 HelloAgentsLLM）
from my_llm import MyLLM

# 加载环境变量
load_dotenv()

# 实例化我们重写的客户端，并指定provider
# provider="modelscope" 会走 MyLLM 里自定义的初始化逻辑
llm = MyLLM(provider="modelscope") 

# 准备消息
# messages 列表格式是 OpenAI 的标准对话格式，类似 JS 的：
# const messages = [{ role: "user", content: "..." }]
messages = [{"role": "user", "content": "你好，请介绍一下你自己。"}]

# 发起调用，think等方法都已从父类继承，无需重写
# think() 返回一个流式响应（generator），逐块产出文本
response_stream = llm.think(messages)

# 打印响应
print("ModelScope Response:")
for chunk in response_stream:
    # chunk在my_llm库中已经打印过一遍，这里只需要pass即可
    # for...in 遍历生成器，类似 JS 的 for await (const chunk of stream)
    # print(chunk, end="", flush=True)
    pass
