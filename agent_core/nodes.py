import os
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill
from .utils import get_available_skills_list

# 初始化 LLM (支持通过环境变量切换模型提供商，如 DeepSeek/火山引擎)
model_name = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")
base_url = os.environ.get("LLM_BASE_URL") # None 意味着使用默认 OpenAI URL
api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")

if not api_key:
    # 简单的 fallback 防止启动报错，实际运行时如果没有 key 会在调用时失败
    print("⚠️ Warning: No API Key found (LLM_API_KEY or OPENAI_API_KEY).")

llm = ChatOpenAI(
    model=model_name,
    temperature=0,
    base_url=base_url,
    api_key=api_key
) 
llm_with_tools = llm.bind_tools(available_tools)

def call_model(state: AgentState):
    """
    核心思考节点：构建结构化 Prompt 并调用 LLM。
    """
    messages = state["messages"]
    active_skills = state.get("active_skills", {})
    available_skills_xml = get_available_skills_list()
    
    # 基础 System Prompt
    system_prompt = f"""<role>
你是一个强大的模块化 CLI 智能体。你具备执行 Shell 命令的能力，并能通过激活外部技能扩展自己的功能。
</role>

<core_strategies>
  <strategy>遇到复杂任务，请优先检查并激活相关技能。</strategy>
  <strategy>【强制思考】在调用工具前，必须在 content 中输出以“🧠 [思考]”开头的内心独白，解释你的判断。</strategy>
  <strategy>【原子工具】修改文件前必须先使用 read_file。严禁在正文中虚构文件内容或执行结果。</strategy>
  <strategy>【严格分步 - 技能】激活技能 (activate_skill) 后，必须等待下一轮对话确认协议加载，严禁在同一轮次中调用该技能下的脚本或工具。</strategy>
  <strategy>【严格分步 - 读写】读取文件 (read_file) 后，必须等待内容返回，严禁在同一轮次中执行 write_file。</strategy>
</core_strategies>

{available_skills_xml}

<current_context>
  工作目录: {os.getcwd()}
</current_context>"""

    # 动态注入已激活技能 (使用更稳健的拼接方式避开 f-string 换行限制)
    if active_skills:
        system_prompt += "\n\n<activated_skills>"
        for skill_name, skill_content in active_skills.items():
            system_prompt += "\n  <skill name=\"" + skill_name + "\">\n    <instructions>\n"
            system_prompt += skill_content
            system_prompt += "\n    </instructions>\n  </skill>"
        system_prompt += "\n</activated_skills>"
    
    clean_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages_payload = [SystemMessage(content=system_prompt)] + clean_messages
    
    response = llm_with_tools.invoke(messages_payload)

    # [硬性拦截逻辑]
    if response.tool_calls:
        tool_names = [tc["name"] for tc in response.tool_calls]
        
        # 拦截 1: 激活与执行并行
        if "activate_skill" in tool_names and len(tool_names) > 1:
            print("\n🛡️ [安全守卫] 检测到激活技能与其他动作并行，强制拦截后续动作。")
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] == "activate_skill"]
            response.content = "🧠 [思考] 我需要先激活技能，待下一轮获知技能协议后再执行具体动作。"

        # 拦截 2: 读写并行
        elif "read_file" in tool_names and "write_file" in tool_names:
            print("\n🛡️ [安全守卫] 检测到并行读写，强制拦截写入操作，确保先读后写。")
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] == "read_file"]
            response.content = "🧠 [思考] 我需要先读取文件内容，确认无误后再进行写入。"

    return {"messages": [response]}

def process_tool_outputs(state: AgentState):
    """后处理节点：处理技能激活的状态更新。"""
    messages = state["messages"]
    current_skills = dict(state.get("active_skills", {}))
    skills_updated = False
    
    last_ai_msg = None
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break
            
    if not last_ai_msg or not last_ai_msg.tool_calls:
        return {}

    id_to_skill = {tc["id"]: tc["args"]["skill_name"] for tc in last_ai_msg.tool_calls if tc["name"] == "activate_skill"}
    if not id_to_skill:
        return {}

    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage): break
        if msg.tool_call_id in id_to_skill:
            skill_name = id_to_skill[msg.tool_call_id]
            if "SYSTEM_INJECTION" in msg.content:
                current_skills[skill_name] = msg.content.replace("SYSTEM_INJECTION: ", "")
                skills_updated = True
    
    return {"active_skills": current_skills} if skills_updated else {}
