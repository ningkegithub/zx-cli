import os
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill
from .utils import get_available_skills_list

# 在核心逻辑模块中初始化 LLM
# 注意: 确保环境变量中设置了 OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini") 
llm_with_tools = llm.bind_tools(available_tools)

def call_model(state: AgentState):
    """
    核心思考节点：组装结构化的 XML Prompt 并调用大模型。
    """
    messages = state["messages"]
    active_skills = state.get("active_skills", {})
    
    # 获取本地可用技能清单 (XML 格式)
    available_skills_xml = get_available_skills_list()
    
    # 组装结构化 System Prompt
    system_prompt = f"""<role>
你是一个强大的模块化 CLI 智能体。你具备执行 Shell 命令的能力，并能通过激活外部技能扩展自己的功能。
</role>

<core_strategies>
  <strategy>遇到复杂任务（如爬虫、PDF 处理、数据分析），请优先检查并激活相关技能，而不是尝试自己写脚本或安装新软件。</strategy>
  <strategy>你具备直接读写文件的原子能力（read_file, write_file）。在尝试修改任何文件之前，必须先使用 read_file 查看其当前内容。</strategy>
  <strategy>对于简单的文件操作（如创建配置文件、修改小段代码、写 Markdown 文档），请直接使用 write_file，不要为了这种小事去写 Python 脚本。</strategy>
  <strategy>必须在 content 字段中输出 [强制思考]，解释你观察到了什么以及为什么选择接下来的动作。</strategy>
  <strategy>严格分步：激活技能 (activate_skill) 后，必须等待下一轮对话确认技能协议已加载，才能执行该技能定义的后续操作（无论是运行脚本还是使用原子工具），严禁在同一轮次中抢跑。</strategy>
  <strategy>依赖阻断：当你使用 read_file 读取文件时，严禁在同一轮次中根据该文件内容执行写操作。你必须等待系统返回文件内容后，在下一轮对话中再进行后续操作。</strategy>
</core_strategies>

{available_skills_xml}

<current_context>
  工作目录: {os.getcwd()}
</current_context>"""

    # 动态注入已激活的技能详情
    if active_skills:
        system_prompt += "\n\n<activated_skills>"
        for skill_name, content in active_skills.items():
            system_prompt += f'\n  <skill name="{skill_name}">\n    <instructions>\n{content}\n    </instructions>\n  </skill>'
        system_prompt += "\n</activated_skills>"
    
    # 过滤掉旧的系统消息，确保上下文清晰
    clean_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages_payload = [SystemMessage(content=system_prompt)] + clean_messages
    
    response = llm_with_tools.invoke(messages_payload)

    # [安全守卫] 硬性拦截：防止 read_file 和 write_file 并行执行
    # 如果模型试图通过“幻觉”在未读取前就写入，强制移除写入操作
    if response.tool_calls:
        tool_names = [tc["name"] for tc in response.tool_calls]
        if "read_file" in tool_names and "write_file" in tool_names:
            print("\n🛡️ [安全守卫] 检测到并行读写，强制拦截写入操作，确保先读后写。")
            # 只保留非 write_file 的工具调用
            response.tool_calls = [tc for tc in response.tool_calls if tc["name"] != "write_file"]

    return {"messages": [response]}

def process_tool_outputs(state: AgentState):
    """
    后处理节点：检查工具执行结果，处理状态更新（如技能激活）。
    它在 ToolNode 之后运行。
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # 确保我们处理的是 ToolMessage 列表（因为 ToolNode 可能一次返回多个）
    # LangGraph 的 ToolNode 会将结果追加到 messages，所以我们要倒序找最近的一批 ToolMessage
    
    # 获取当前已激活的技能字典
    current_skills = dict(state.get("active_skills", {}))
    skills_updated = False
    
    # 重新设计策略：
    # 核心逻辑：通过 tool_call_id 将 ToolMessage 与 AIMessage 中的工具调用关联起来。
    
    # 1. 找到最近的一个 AIMessage (即发起工具调用的源头)
    last_ai_msg = None
    for msg in reversed(messages):
        if isinstance(msg, SystemMessage): continue # skip
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break
            
    if not last_ai_msg or not last_ai_msg.tool_calls:
        return {}

    # 2. 建立 ID 到 skill_name 的映射表
    # 这一步是为了确保我们只处理 activate_skill 的结果，并且能拿到对应的技能名
    id_to_skill = {}
    for tc in last_ai_msg.tool_calls:
        if tc["name"] == "activate_skill":
            id_to_skill[tc["id"]] = tc["args"]["skill_name"]

    if not id_to_skill:
        return {}

    # 3. 扫描对应的 ToolMessage 并提取协议内容
    for msg in reversed(messages):
        if not isinstance(msg, ToolMessage):
            break
        
        # 只有当消息ID匹配且包含特定的协议注入标识时，才更新状态
        if msg.tool_call_id in id_to_skill:
            skill_name = id_to_skill[msg.tool_call_id]
            if "SYSTEM_INJECTION" in msg.content:
                content = msg.content.replace("SYSTEM_INJECTION: ", "")
                current_skills[skill_name] = content
                skills_updated = True
    
    if skills_updated:
        return {"active_skills": current_skills}
    
    return {}
