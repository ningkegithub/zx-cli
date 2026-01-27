import os
from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from .state import AgentState
from .tools import available_tools, activate_skill

# Init LLM within the core logic module
# Note: Ensure OPENAI_API_KEY is set in environment
llm = ChatOpenAI(model="gpt-4o-mini") 
llm_with_tools = llm.bind_tools(available_tools)

def call_model(state: AgentState):
    messages = state["messages"]
    active_skills = state.get("active_skills", "")
    
    system_prompt = (
        "You are a powerful CLI Agent capable of using shell commands.\n"
        "If a user request is complex, check if you can activate a skill first.\n"
        "Current working directory: " + os.getcwd()
    )
    
    if active_skills:
        system_prompt += f"\n\n=== 🌟 ACTIVE SKILLS ===\n{active_skills}\n========================"
    
    # Filter out old SystemMessages to keep context clean
    clean_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    messages_payload = [SystemMessage(content=system_prompt)] + clean_messages
    
    response = llm_with_tools.invoke(messages_payload)
    return {"messages": [response]}

def handle_skill_activation(state: AgentState):
    last_message = state["messages"][-1]
    tool_outputs = []
    new_skill_content = None
    
    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "activate_skill":
            result = activate_skill.invoke(tool_call["args"])
            if "SYSTEM_INJECTION" in result:
                content = result.replace("SYSTEM_INJECTION: ", "")
                new_skill_content = content
                feedback = f"✅ Skill '{tool_call['args']['skill_name']}' ACTIVATED."
            else:
                feedback = result
            tool_outputs.append(ToolMessage(content=feedback, tool_call_id=tool_call["id"]))
    
    updates = {"messages": tool_outputs}
    if new_skill_content:
        updates["active_skills"] = new_skill_content
    return updates
