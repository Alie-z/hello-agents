"""
本文件作用：测试 Plan-and-Solve Agent（计划与求解智能体）。

测试内容：
- 用一个数学文字题测试"先规划后执行"的完整流程
"""
# test_plan_solve_agent.py
from dotenv import load_dotenv
# 从框架核心模块导入 LLM 类
from hello_agents.core.llm import HelloAgentsLLM
from my_plan_solve_agent import MyPlanAndSolveAgent

# 加载环境变量
load_dotenv()

# 创建LLM实例
llm = HelloAgentsLLM()

# 创建自定义PlanAndSolveAgent
agent = MyPlanAndSolveAgent(
    name="我的规划执行助手",
    llm=llm
)

# 测试复杂问题
# 这种多步数学题适合 Plan-and-Solve：先拆成子步骤，再逐步求解
question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"

# agent.run() 会先调规划器拆步骤，再调执行器逐步完成
result = agent.run(question)
print(f"\n最终结果: {result}")

# 查看对话历史
print(f"对话历史: {len(agent.get_history())} 条消息")
