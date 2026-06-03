"""
本文件作用：测试 Reflection Agent（反思智能体），包括通用版和自定义代码生成版。

测试内容：
- 通用反思助手：写文章任务
- 代码生成助手：用自定义 prompt 做代码 review + 优化
"""
# test_reflection_agent.py
from dotenv import load_dotenv
from hello_agents import HelloAgentsLLM
from my_reflection_agent import MyReflectionAgent

load_dotenv()
llm = HelloAgentsLLM()

# 使用默认通用提示词
general_agent = MyReflectionAgent(name="我的反思助手", llm=llm)

# 使用自定义代码生成提示词（类似第四章）
# 字典定义多个提示词模板，每个模板用于不同阶段
# 类似 JS 的 const codePrompts = { initial: "...", reflect: "...", refine: "..." }
code_prompts = {
    "initial": "你是Python专家，请编写函数：{task}",
    "reflect": "请审查代码的算法效率：\n任务：{task}\n代码：{content}",
    "refine": "请根据反馈优化代码：\n任务：{task}\n反馈：{feedback}"
}
code_agent = MyReflectionAgent(
    name="我的代码生成助手",
    llm=llm,
    # custom_prompts 自定义各阶段的提示词
    custom_prompts=code_prompts
)

# 测试使用
# .run() 会自动执行"生成→反思→优化"的迭代循环
result = general_agent.run("写一篇关于人工智能发展历程的简短文章")
print(f"最终结果: {result}")
