import os
import subprocess
import sys
from langchain_core.tools import tool
from .utils import INTERNAL_SKILLS_DIR, USER_SKILLS_DIR

@tool
def run_shell(command: str):
    """执行 Shell 命令。例如：'ls -F', 'python3 script.py'。"""
    
    # [自动修复] 确保 Python 脚本在相同的虚拟环境 (venv) 中运行
    cmd_stripped = command.strip()
    if cmd_stripped.startswith("python3 ") or cmd_stripped.startswith("python "):
        parts = cmd_stripped.split(" ", 1)
        if len(parts) > 1:
            # 将 'python'/'python3' 替换为当前解释器的绝对路径
            original_cmd = command
            command = f"{sys.executable} {parts[1]}"
            # print(f"🔄 [环境修复] 重定向至当前 Python: {sys.executable}") # 暂时注释，交给 UI 层处理

    # print(f"\n💻 [Shell] 执行中: {command}") # 移除直接打印，避免破坏 Rich Live UI
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        if len(output) > 2000:
            output = output[:2000] + "...(truncated)"
        return output
    except Exception as e:
        return f"命令执行错误: {e}"

@tool
def activate_skill(skill_name: str):
    """激活特殊技能。例如：'imagetopdf', 'web_scraper'。"""
    # print(f"\n⚡️ [工具] 激活技能: {skill_name}...") # 移除直接打印
    
    # 搜索优先级：项目内置技能 > 用户自定义技能
    search_paths = [
        os.path.join(INTERNAL_SKILLS_DIR, skill_name, "SKILL.md"),
        os.path.join(USER_SKILLS_DIR, skill_name, "SKILL.md")
    ]
    
    target_file = None
    skill_base_dir = None
    
    for path in search_paths:
        if os.path.exists(path):
            target_file = path
            skill_base_dir = os.path.dirname(path)
            break
            
    if target_file and skill_base_dir:
        try:
            with open(target_file, "r") as f:
                content = f.read()
            
            # [关键] 动态变量注入
            # 将 {SKILL_DIR} 替换为技能的真实绝对路径
            # 这样 Agent 无论在哪里运行，都能找到 scripts/ 下的脚本
            injected_content = content.replace("{SKILL_DIR}", skill_base_dir)
            
            return f"SYSTEM_INJECTION: {injected_content}"
        except Exception as e:
            return f"读取技能文件错误: {e}"
    else:
        return f"错误: 本地未找到技能 '{skill_name}'。"

@tool
def read_file(file_path: str):
    """读取指定文件的内容。在尝试修改或分析现有代码/配置前，请先读取它。"""
    if not os.path.exists(file_path):
        return f"错误: 未找到文件 '{file_path}'。"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # 默认读取前 500 行，防止超出上下文限制
            lines = f.readlines()
            content = "".join(lines[:500])
            if len(lines) > 500:
                content += f"\n\n...(由于文件过长，已截断，共 {len(lines)} 行)..."
            return content
    except Exception as e:
        return f"读取文件出错: {e}"

@tool
def write_file(file_path: str, content: str):
    """将文本内容写入指定文件（完全覆盖）。如果文件不存在则创建，如果目录不存在也会自动创建。"""
    try:
        # 自动创建父级目录
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功写入文件: {file_path}"
    except Exception as e:
        return f"写入文件出错: {e}"

# 导出工具列表以供绑定
available_tools = [run_shell, activate_skill, read_file, write_file]
