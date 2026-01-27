import os
import sys
import operator
import subprocess
from typing import Annotated, List, TypedDict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

# --- 0. Configuration ---
# Note: Ensure OPENAI_API_KEY is set in your environment variables.
SKILL_PATH = os.path.expanduser("~/.gemini/skills/image-to-pdf/SKILL.md")

# --- 1. State ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    active_skills: str

# --- 2. Tools ---

@tool
def run_shell(command: str):
    """Execute shell commands. e.g. 'ls -F', 'python3 script.py'."""
    print(f"\n💻 [Shell] Executing: {command}")
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
        return f"Error executing command: {e}"

@tool
def activate_skill(skill_name: str):
    """Activate a special skill. e.g. 'imagetopdf'."""
    print(f"\n⚡️ [Tool] Activating skill: {skill_name}...")
    
    target_path = SKILL_PATH 
    
    if skill_name == "imagetopdf":
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                content = f.read()
            return f"SYSTEM_INJECTION: {content}"
        else:
            return f"Error: Skill definition file not found at {target_path}"
    else:
        return f"Error: Skill '{skill_name}' is not installed locally."

# --- 3. Init ---
llm = ChatOpenAI(model="gpt-4o-mini")
tools = [run_shell, activate_skill]
llm_with_tools = llm.bind_tools(tools)

# --- 4. Nodes ---

def call_model(state: AgentState):
    global llm_with_tools
    
    messages = state["messages"]
    active_skills = state.get("active_skills", "")
    
    system_prompt = (
        "You are a powerful CLI Agent capable of using shell commands.\n"
        "If a user request is complex, check if you can activate a skill first.\n"
        "Current working directory: " + os.getcwd()
    )
    
    if active_skills:
        system_prompt += f"\n\n=== 🌟 ACTIVE SKILLS ===\n{active_skills}\n========================"
    
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

# --- 5. Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("agent", call_model)
workflow.add_node("skill_handler", handle_skill_activation)
workflow.add_node("tools", ToolNode([run_shell]))

workflow.set_entry_point("agent")

def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if not last_message.tool_calls:
        return END
    
    if any(tc["name"] == "activate_skill" for tc in last_message.tool_calls):
        return "skill_handler"
        
    return "tools"

workflow.add_conditional_edges("agent", should_continue, ["skill_handler", "tools", END])
workflow.add_edge("skill_handler", "agent")
workflow.add_edge("tools", "agent")

app = workflow.compile()

# --- 6. Main Loop ---
def main():
    print("🤖 Real Agent CLI (v4 - Clean)")
    print("----------------------------")
    print("Tip: Try asking 'Merge images in current folder to PDF'.")
    print("Type 'exit' to quit.\n")
    
    chat_history = []
    active_skills = ""

    while True:
        try:
            user_input = input("User> ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            inputs = {
                "messages": chat_history + [HumanMessage(content=user_input)],
                "active_skills": active_skills
            }
            
            print("   (Thinking...)")
            for event in app.stream(inputs, stream_mode="values"):
                last_msg = event["messages"][-1]
                active_skills = event.get("active_skills", active_skills)
                
                if isinstance(last_msg, AIMessage):
                    if last_msg.tool_calls:
                        for tc in last_msg.tool_calls:
                            print(f"   🤖 Action: {tc['name']}({tc['args']})")
                    elif last_msg.content:
                        print(f"Agent> {last_msg.content}")
                
            chat_history = event["messages"]
            print("")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()