# 快速上手指南

## 前置条件

- Python 3.10+
- LLM API 密钥（支持 OpenAI 兼容接口）

---

## 第一步：激活虚拟环境

```bash
# 在项目根目录执行
source venv/bin/activate
```

激活后命令行前会出现 `(venv)` 提示符。每次打开新终端都需要重新激活。

> 退出虚拟环境：`deactivate`

---

## 第二步：安装依赖

```bash
pip install hello-agents
```

---

## 第三步：配置 API 密钥

```bash
cd code/chapter7
cp .env.example .env
```

编辑 `.env`，填入你的密钥：

```env
LLM_MODEL_ID="gpt-4o-mini"
LLM_API_KEY="sk-xxxxxxxxxxxxxxxx"
LLM_BASE_URL="https://api.openai.com/v1"
LLM_TIMEOUT=60
```

常见国内服务商地址：

| 服务商 | BASE_URL |
|--------|----------|
| 阿里云百炼 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 智谱 AI | `https://open.bigmodel.cn/api/paas/v4` |
| 月之暗面 Kimi | `https://api.moonshot.cn/v1` |

---

## 第四步：运行示例

> `my_simple_agent.py` 只定义类，直接运行没有输出，需运行测试文件。

```bash
# 在 code/chapter7 目录下
python test_simple_agent.py      # SimpleAgent 完整功能测试（推荐先跑这个）
python test_my_calculator.py     # 计算器工具测试
python test_react_agent.py       # ReAct Agent 测试
python test_reflection_agent.py  # Reflection Agent 测试
python my_main.py                # LLM 调用演示
```

---

## 常见报错

| 报错 | 原因 | 解决 |
|------|------|------|
| `ModuleNotFoundError: No module named 'hello_agents'` | 未激活 venv | `source venv/bin/activate` |
| `ModuleNotFoundError: No module named 'dotenv'` | 未激活 venv | `source venv/bin/activate` |
| `zsh: command not found: python` | 系统无 `python` 命令 | 激活 venv 后用 `python`，或用 `python3` |
| `HelloAgentsException: 必须提供API密钥` | `.env` 未配置 | 检查 `.env` 文件是否存在且密钥正确 |
| `AuthenticationError` | API Key 错误 | 检查 `LLM_API_KEY` |
| `Connection refused` | BASE_URL 错误 | 确认地址末尾是否需要 `/v1` |
| 运行 `my_simple_agent.py` 无输出 | 该文件只定义类 | 改运行 `test_simple_agent.py` |
