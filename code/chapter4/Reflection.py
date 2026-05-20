"""
本文件作用：实现 Reflection（反思）模式的智能体。
Reflection 模式让 Agent 先生成一个初始结果，然后自己审查并给出反馈，
再根据反馈改进，如此迭代直到满意。类似于"写代码 → code review → 改进"的循环。

主要内容：
- Memory：记忆模块，存储每轮的执行结果和反思反馈
- ReflectionAgent：反思智能体，驱动"生成→反思→优化"的迭代循环
- 三个提示词模板：初始执行、反思、优化

依赖说明：
- typing：类型注解，类似 TS 的类型系统
- llm_client：本项目的 LLM 客户端封装
"""
from typing import List, Dict, Any  # 类型注解，类似 TS 的 Array<T>、Record<K, V>、any
# 假设 llm_client.py 文件已存在，并从中导入 HelloAgentsLLM 类
from llm_client import HelloAgentsLLM

# --- 模块 1: 记忆模块 ---

class Memory:
    """
    一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹。

    类似前端里的 state 管理——存储每次操作的历史，供后续步骤回溯参考。
    相当于 JS 里的：
    class Memory {
      records: Array<{type: string, content: string}> = [];
    }
    """
    def __init__(self):
        # 初始化一个空列表来存储所有记录
        # List[Dict[str, Any]] 类似 TS 的 Array<{ type: string; content: any }>
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        """
        向记忆中添加一条新记录。

        参数:
        - record_type (str): 记录的类型 ('execution' 或 'reflection')。
        - content (str): 记录的具体内容 (例如，生成的代码或反思的反馈)。
        """
        # .append() 向列表末尾添加元素，类似 JS 的 array.push()
        self.records.append({"type": record_type, "content": content})
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        """
        将所有记忆记录格式化为一个连贯的字符串文本，用于构建提示词。

        返回：
            str: 所有历史记录拼成的文本
        """
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- 上一轮尝试 (代码) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        # .strip() 去除首尾空白字符，类似 JS 的 str.trim()
        return trajectory.strip()

    def get_last_execution(self) -> str:
        """
        获取最近一次的执行结果 (例如，最新生成的代码)。

        返回：
            str | None: 最近一次 execution 类型的记录内容
        """
        # reversed() 反向遍历列表，类似 JS 的 [...arr].reverse().find(...)
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None

# --- 模块 2: Reflection 智能体 ---

# 1. 初始执行提示词——让 LLM 生成第一版代码
INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

# 2. 反思提示词——让 LLM 扮演 code reviewer 角色审查代码
REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在**算法效率**上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种**算法上更优**的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答"无需改进"。

请直接输出你的反馈，不要包含任何额外的解释。
"""

# 3. 优化提示词——让 LLM 根据 reviewer 的反馈重写代码
REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_code_attempt}

# 评审员的反馈:
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""

class ReflectionAgent:
    """
    Reflection 智能体：实现"生成 → 反思 → 优化"的迭代循环。

    工作流程类似前端的 CI/CD pipeline 或自动化 lint + fix：
    1. 先写出初版代码
    2. 用另一个 "reviewer" 角色审查
    3. 根据审查意见改进
    4. 重复 2-3 直到 reviewer 说"无需改进"或达到最大轮数
    """
    def __init__(self, llm_client, max_iterations=3):
        """
        参数：
            llm_client: LLM 客户端实例
            max_iterations (int): 最大迭代轮数，防止无限循环
        """
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        """
        运行反思智能体。

        参数：
            task (str): 用户的任务描述（如"编写一个找素数的函数"）

        返回：
            str: 最终优化后的代码
        """
        print(f"\n--- 开始处理任务 ---\n任务: {task}")

        # --- 1. 初始执行 ---
        print("\n--- 正在进行初始尝试 ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # --- 2. 迭代循环：反思与优化 ---
        # range(n) 生成 0 到 n-1 的序列，类似 JS 的 for (let i = 0; i < n; i++)
        for i in range(self.max_iterations):
            print(f"\n--- 第 {i+1}/{self.max_iterations} 轮迭代 ---")

            # a. 反思：让 LLM 作为 reviewer 审查当前代码
            print("\n-> 正在进行反思...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. 检查是否需要停止：如果 reviewer 说"无需改进"就结束
            # "in" 检查子串是否存在，类似 JS 的 str.includes("无需改进")
            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ 反思认为代码已无需改进，任务完成。")
                break

            # c. 优化：根据反馈生成新版代码
            print("\n-> 正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)
        
        final_code = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终生成的代码:\n{final_code}")
        return final_code

    def _get_llm_response(self, prompt: str) -> str:
        """
        辅助方法：调用 LLM 并获取完整响应。

        参数：
            prompt (str): 发送给 LLM 的提示词

        返回：
            str: LLM 的响应文本
        """
        messages = [{"role": "user", "content": prompt}]
        # or "" 确保返回值不为 None，类似 JS 的 ?? ""
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text

# --- 主程序入口 ---
if __name__ == '__main__':
    # 仅在直接运行此文件时执行，类似 Node 里的 if (require.main === module)

    # 1. 初始化LLM客户端 (请确保你的 .env 和 llm_client.py 文件配置正确)
    try:
        llm_client = HelloAgentsLLM()
    except Exception as e:
        print(f"初始化LLM客户端时出错: {e}")
        exit()  # 退出程序，类似 JS 的 process.exit()

    # 2. 初始化 Reflection 智能体，设置最多迭代2轮
    agent = ReflectionAgent(llm_client, max_iterations=2)

    # 3. 定义任务并运行智能体
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)
