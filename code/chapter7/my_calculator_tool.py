"""
本文件作用：自定义计算器工具，用 AST（抽象语法树）安全地计算数学表达式。

主要内容：
- my_calculate：安全的数学计算函数，支持 +、-、*、/、sqrt
- _eval_node：递归求值 AST 节点（内部辅助函数）
- create_calculator_registry：创建包含计算器的工具注册表

依赖说明：
- ast：Python 标准库，把字符串解析为抽象语法树，实现安全求值（不用危险的 eval）
- operator：Python 标准库，提供运算符的函数版本（如 operator.add 就是 + 的函数形式）
- math：Python 标准库，数学函数（sqrt、pi 等）
"""
# my_calculator_tool.py
# ast 模块把代码字符串解析成树形结构，可以安全地只处理数学表达式
# 类似 JS 里用 Babel AST 解析代码，但这里只关心表达式节点
import ast
# operator 模块把运算符包装成函数：operator.add(a, b) 等价于 a + b
import operator
import math
from hello_agents import ToolRegistry

def my_calculate(expression: str) -> str:
    """
    简单的数学计算函数。安全解析并计算表达式。

    参数：
        expression (str): 数学表达式字符串，如 "2 + 3" 或 "sqrt(16)"

    返回：
        str: 计算结果的字符串形式
    """
    # .strip() 去除首尾空白，类似 JS 的 .trim()
    if not expression.strip():
        return "计算表达式不能为空"

    # 支持的基本运算
    # 字典把 AST 节点类型映射到对应的运算函数
    # 类似 JS 的 Map：new Map([[ast.Add, (a, b) => a + b], ...])
    operators = {
        ast.Add: operator.add,      # +
        ast.Sub: operator.sub,      # -
        ast.Mult: operator.mul,     # *
        ast.Div: operator.truediv,  # /
    }

    # 支持的基本函数
    functions = {
        'sqrt': math.sqrt,
        'pi': math.pi,
    }

    try:
        # ast.parse() 把表达式字符串解析成 AST（抽象语法树）
        # mode='eval' 表示只接受单个表达式（不是完整的 Python 代码）
        # 这样做比 eval() 安全得多——只能计算数学，不能执行任意代码
        node = ast.parse(expression, mode='eval')
        result = _eval_node(node.body, operators, functions)
        return str(result)
    except:
        # 裸 except 捕获所有异常（包括 BaseException）
        # ⚠️ 生产代码建议用 except Exception 更精确
        return "计算失败，请检查表达式格式"

def _eval_node(node, operators, functions):
    """
    递归求值 AST 节点。

    这是一个递归函数：根据节点类型分别处理数字、二元运算、函数调用等。
    类似 JS 里递归遍历 AST 树的模式。

    参数：
        node: AST 节点
        operators (dict): 支持的运算符映射
        functions (dict): 支持的函数映射

    返回：
        数值类型: 计算结果
    """
    # isinstance() 判断对象类型，类似 JS 的 node instanceof Constant
    if isinstance(node, ast.Constant):
        # 数字字面量节点，直接返回值
        return node.value
    elif isinstance(node, ast.BinOp):
        # 二元运算节点（如 a + b），递归求值左右子节点
        left = _eval_node(node.left, operators, functions)
        right = _eval_node(node.right, operators, functions)
        # type(node.op) 获取运算符类型（ast.Add / ast.Sub 等）
        op = operators.get(type(node.op))
        return op(left, right)
    elif isinstance(node, ast.Call):
        # 函数调用节点（如 sqrt(16)）
        func_name = node.func.id
        if func_name in functions:
            # 列表推导式递归求值所有参数
            # 类似 JS：node.args.map(arg => evalNode(arg))
            args = [_eval_node(arg, operators, functions) for arg in node.args]
            # *args 解包列表作为位置参数传入，类似 JS 的 func(...args)
            return functions[func_name](*args)
    elif isinstance(node, ast.Name):
        # 变量名节点（如 pi），从 functions 字典中查找常量值
        if node.id in functions:
            return functions[node.id]

def create_calculator_registry():
    """
    创建包含计算器的工具注册表。

    返回：
        ToolRegistry: 注册了 my_calculator 工具的注册表实例
    """
    registry = ToolRegistry()

    # 注册计算器函数
    # register_function 把普通函数注册为 Agent 可调用的"工具"
    registry.register_function(
        name="my_calculator",
        description="简单的数学计算工具，支持基本运算(+,-,*,/)和sqrt函数",
        func=my_calculate
    )

    return registry
