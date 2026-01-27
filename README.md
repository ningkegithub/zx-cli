# Agent CLI

一个基于 LangGraph 和 OpenAI GPT-4o 的模块化智能体 CLI。

## 功能特性
- **动态技能加载**：通过 `activate_skill` 动态读取本地 Skill 定义。
- **Shell 执行**：支持执行真实 Shell 命令。
- **状态机架构**：清晰的图结构管理状态流转。

## 目录结构
- `main.py`: 程序入口。
- `agent_core/`: 核心逻辑包。
    - `graph.py`: 状态图定义。
    - `nodes.py`: 节点逻辑 (LLM调用, 技能处理)。
    - `tools.py`: 工具定义。

## 快速开始

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 设置 Key：
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```

3. 运行：
   ```bash
   python3 main.py
   ```
