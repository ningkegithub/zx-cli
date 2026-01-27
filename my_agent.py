import operator
from typing import Annotated, List, TypedDict, Union, Dict, Any

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# --- 1. 定义状态 (State) ---
class AgentState(TypedDict):
    # 消息历史：自动追加
    messages: Annotated[List[BaseMessage], operator.add]
    # 动态技能槽位：覆盖更新
    active_skills: str

# --- 2. 定义工具 (Tools) ---
@tool
def get_weather(city: str):
    """查询指定城市的天气。"""
    print(f"   [ToolExec] 正在查询 {city} 的天气...")
    return f"{city} 天气晴朗，25℃"

@tool
def activate_skill(skill_name: str):
    """激活一个特殊技能 (poet 或 coder)。"""
    print(f"   [ToolExec] 正在激活技能: {skill_name}...")
    
    if skill_name == "poet":
        return "SYSTEM_INJECTION: [技能: 诗人] 你现在是李白转世。所有回答必须是七言绝句，且必须押韵。"
    elif skill_name == "coder":
        return "SYSTEM_INJECTION: [技能: 程序员] 你现在是 Python 专家。所有回答必须包含代码块。"
    else:
        return f"Error: 技能 '{skill_name}' 未找到。"

# --- 3. 模拟 LLM (Mock LLM) ---
# 为了演示方便，我们不用真实的 API Key，而是用规则模拟 LLM 的决策
# 在真实场景中，这里应该替换为: llm = ChatOpenAI(model="gpt-4o").bind_tools(tools)
class MockLLM:
    def invoke(self, messages: List[BaseMessage]):
        last_msg = messages[-1]
        content = last_msg.content if isinstance(last_msg, HumanMessage) else ""
        system_prompt = next((m.content for m in messages if isinstance(m, SystemMessage)), "")
        
        print(f"\n🤖 [LLM 思考中]...")
        print(f"   [Context] System Prompt 长度: {len(system_prompt)} chars")
        if "技能" in system_prompt:
            print(f"   [Context] ⚠️ 发现激活的技能指令！")

        # 简单的规则引擎模拟 LLM 决策
        if "天气" in content:
            # 模拟 LLM 决定调用 get_weather
            return AIMessage(
                content="",
                tool_calls=[{"name": "get_weather", "args": {"city": "北京"}, "id": "call_weather_1"}]
            )
        elif "技能" in content or "激活" in content:
            # 模拟 LLM 决定调用 activate_skill
            skill = "poet" if "诗人" in content else "coder"
            return AIMessage(
                content="",
                tool_calls=[{"name": "activate_skill", "args": {"skill_name": skill}, "id": "call_skill_1"}]
            )
        else:
            # 普通对话，根据 System Prompt 模拟不同的人格回复
            if "[技能: 诗人]" in system_prompt:
                return AIMessage(content="床前明月光，疑是地上霜。\n举头望明月，低头思故乡。")
            elif "[技能: 程序员]" in system_prompt:
                return AIMessage(content="```python\nprint('Hello World')\n```")
            else:
                return AIMessage(content=f"收到了：{content}。我是普通助手。" )

# 初始化 Mock LLM
llm = MockLLM()
tools = [get_weather, activate_skill]

# --- 4. 定义节点逻辑 (Nodes) ---

def call_model(state: AgentState):
    """核心思考节点：组装 Prompt 并调用 LLM"""
    messages = state["messages"]
    active_skills = state.get("active_skills", "")
    
    # [关键] 动态上下文编排 (Context Orchestration)
    # 如果有激活的技能，将其注入到 System Prompt
    system_instruction = "你是一个智能助手。"
    if active_skills:
        system_instruction += f"\n\n=== 🌟 动态技能生效 ===\n{active_skills}\n====================="
    
    # 构造临时的消息列表发给 LLM
    # 注意：SystemMessage 放在最前面
    messages_with_sys = [SystemMessage(content=system_instruction)] + messages
    
    response = llm.invoke(messages_with_sys)
    return {"messages": [response]}

def handle_skill_activation(state: AgentState):
    """专门处理 activate_skill 的节点，用于更新 active_skills 状态"""
    last_message = state["messages"][-1]
    
    tool_outputs = []
    new_skill_content = None
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "activate_skill":
            # 执行工具
            result = activate_skill.invoke(tool_call["args"])
            
            # [关键] 解析工具返回，更新全局状态
            if "SYSTEM_INJECTION" in result:
                new_skill_content = result
                user_feedback = f"技能已激活！({tool_call['args']['skill_name']})"
            else:
                user_feedback = result
                
            tool_outputs.append(
                ToolMessage(content=user_feedback, tool_call_id=tool_call["id"])
            )
    
    # 如果技能有更新，返回新的 active_skills
    if new_skill_content:
        return {"messages": tool_outputs, "active_skills": new_skill_content}
    
    return {"messages": tool_outputs}

# --- 5. 构建图 (Graph Construction) ---

workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("agent", call_model)
workflow.add_node("skill_handler", handle_skill_activation)
workflow.add_node("tools", ToolNode([get_weather]))

# 设置入口
workflow.set_entry_point("agent")

# 定义路由逻辑
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    
    # 如果没有工具调用，结束
    if not last_message.tool_calls:
        return END
    
    # 如果是激活技能，走 skill_handler
    if last_message.tool_calls[0]["name"] == "activate_skill":
        return "skill_handler"
    
    # 否则走普通工具
    return "tools"

# 添加边
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "skill_handler": "skill_handler",
        "tools": "tools",
        END: END
    }
)

workflow.add_edge("skill_handler", "agent")
workflow.add_edge("tools", "agent")

app = workflow.compile()

# --- 6. 运行测试 (Simulation) ---

def run_demo():
    print("🚀 启动主 Agent (LangGraph 版)...")
    
    # 初始状态
    current_state = {"messages": [], "active_skills": ""}
    
    # 场景 1: 普通对话
    print("--- User: 激活“诗人”技能 ---")
    inputs = {"messages": [HumanMessage(content="帮我激活诗人技能")]}
    # 合并输入到当前状态
    current_state["messages"].extend(inputs["messages"])
    
    # 运行图
    for event in app.stream(current_state, stream_mode="values"):
        # 这里 stream 会返回每一步的状态
        last_msg = event["messages"][-1]
        # 更新我们模拟的外部状态
        current_state = event 
        
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
            print(f"🤖 Agent 回复: {last_msg.content}")
    
    print("\n--- User: 现在，写一首关于 AI 的诗 ---")
    inputs = {"messages": [HumanMessage(content="写一首关于 AI 的诗")]}
    current_state["messages"].extend(inputs["messages"])
    
    for event in app.stream(current_state, stream_mode="values"):
        last_msg = event["messages"][-1]
        if isinstance(last_msg, AIMessage) and not last_msg.tool_calls:
             print(f"🤖 Agent 回复: {last_msg.content}")

if __name__ == "__main__":
    run_demo()
