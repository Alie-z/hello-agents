"""
本文件作用：实现 Plan-and-Solve（计划与求解）模式的智能体。
这种模式把复杂问题拆成两步：先让 LLM 制定计划（拆分子任务），再让 LLM 按计划逐步执行。

主要内容：
- PLANNER_PROMPT_TEMPLATE：规划器的提示词模板
- Planner：规划器类，让 LLM 把问题拆成步骤列表
- EXECUTOR_PROMPT_TEMPLATE：执行器的提示词模板
- Executor：执行器类，让 LLM 逐步解决每个子任务
- PlanAndSolveAgent：整合规划器和执行器的智能体

依赖说明：
- ast：Python 标准库，用于安全解析字符串为 Python 数据结构（如把 "[1,2,3]" 变成列表）
- llm_client：本项目的 LLM 客户端封装
"""
import os
import ast  # Abstract Syntax Trees，这里用 ast.literal_eval() 安全解析字符串为 Python 对象
    # 类似 JS 的 JSON.parse()，但能解析 Python 语法（如单引号字符串）
from llm_client import HelloAgentsLLM
from dotenv import load_dotenv
from typing import List, Dict  # 类型注解，类似 TS 的 Array<string> 和 Record<string, string>

# 加载 .env 文件中的环境变量，处理文件不存在异常
try:
    load_dotenv()
except FileNotFoundError:
    print("警告：未找到 .env 文件，将使用系统环境变量。")
except Exception as e:
    print(f"警告：加载 .env 文件时出错: {e}")

# --- 1. LLM客户端定义 ---
# 假设你已经有llm_client.py文件，里面定义了HelloAgentsLLM类

# --- 2. 规划器 (Planner) 定义 ---
# 提示词模板：告诉 LLM 把用户问题拆成步骤列表，输出格式为 Python 列表字符串
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    """
    规划器：把复杂问题拆解成有序的子任务列表。

    类似前端里把一个复杂的异步流程拆成 Promise 链或 step wizard 的各步骤。
    """
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        """
        调用 LLM 为问题生成执行计划。

        参数：
            question (str): 用户的复杂问题

        返回：
            list[str]: 步骤列表，如 ["步骤1", "步骤2", ...]
        """
        # .format() 填充模板中的占位符，类似 JS 模板字符串的变量插入
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]
        
        print("--- 正在生成计划 ---")
        response_text = self.llm_client.think(messages=messages) or ""
        # or "" 确保即使 think() 返回 None 也不会报错，类似 JS 的 ?? ""
        print(f"✅ 计划已生成:\n{response_text}")
        
        try:
            # 从 LLM 回复中提取 ```python ... ``` 代码块里的内容
            # .split("```python")[1] 取第一个 ```python 后面的部分
            # .split("```")[0] 再取 ``` 前面的部分
            # 类似 JS：response.split("```python")[1].split("```")[0].trim()
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            # ast.literal_eval() 安全地把字符串 '["a", "b"]' 解析成真正的列表
            # 比 eval() 安全——只能解析字面值，不会执行任意代码
            # 类似 JS 的 JSON.parse()，但支持 Python 语法
            plan = ast.literal_eval(plan_str)
            # isinstance() 检查类型，类似 JS 的 Array.isArray(plan)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            # 捕获多种异常类型，类似 JS 的 catch(e) { if (e instanceof X || e instanceof Y) }
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

# --- 3. 执行器 (Executor) 定义 ---
# 提示词模板：给 LLM 完整上下文，让它专注解决当前步骤
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""

class Executor:
    """
    执行器：按照计划逐步调用 LLM 完成每个子任务。

    类似前端里的 step-by-step wizard 或 pipeline 处理器：
    每个步骤的输出会累积到 history 中，作为下一步的上下文。
    """
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        """
        逐步执行计划中的每个子任务。

        参数：
            question (str): 原始问题
            plan (list[str]): 规划器生成的步骤列表

        返回：
            str: 最后一步的执行结果（即最终答案）
        """
        history = ""
        final_answer = ""
        
        print("\n--- 正在执行计划 ---")
        # enumerate(plan, 1) 从 1 开始编号遍历列表
        # 类似 JS 的 plan.forEach((step, index) => { const i = index + 1; ... })
        for i, step in enumerate(plan, 1):
            print(f"\n-> 正在执行步骤 {i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan, history=history if history else "无", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]
            
            response_text = self.llm_client.think(messages=messages) or ""
            
            # 把当前步骤的结果追加到历史中，下一步能看到前面的成果
            # += 字符串拼接，类似 JS 的 history += `步骤 ${i}: ${step}\n结果: ${response}\n\n`
            history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ 步骤 {i} 已完成，结果: {final_answer}")
            
        return final_answer

# --- 4. 智能体 (Agent) 整合 ---
class PlanAndSolveAgent:
    """
    Plan-and-Solve 智能体：先规划后执行。

    整体流程：
    用户问题 → Planner.plan() 生成步骤 → Executor.execute() 逐步执行 → 最终答案
    """
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        """
        运行智能体：规划 + 执行。

        参数：
            question (str): 用户的复杂问题
        """
        print(f"\n--- 开始处理问题 ---\n问题: {question}")
        plan = self.planner.plan(question)
        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return
        final_answer = self.executor.execute(question, plan)
        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")

# --- 5. 主函数入口 ---
if __name__ == '__main__':
    # 仅在直接运行此文件时执行，类似 Node 里的 if (require.main === module)
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        print(e)
