from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from .state import AgentState
from .nodes import call_model, handle_skill_activation
from .tools import available_tools

def build_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("skill_handler", handle_skill_activation)
    
    # Standard ToolNode handles everything EXCEPT activate_skill (which is handled by skill_handler)
    # Actually, ToolNode will try to handle all tools in the list.
    # We need to make sure ToolNode only handles 'run_shell'.
    # Or, we can let skill_handler handle activate_skill and let ToolNode handle the rest.
    # However, ToolNode automatically executes based on tool_calls.
    # Strategy: We use a custom conditional edge.
    
    # Filter tools for the standard node (only run_shell)
    standard_tools = [t for t in available_tools if t.name != "activate_skill"]
    workflow.add_node("tools", ToolNode(standard_tools))

    # Set Entry Point
    workflow.set_entry_point("agent")

    # Conditional Logic
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if not last_message.tool_calls:
            return END
        
        # Check if activate_skill is called
        if any(tc["name"] == "activate_skill" for tc in last_message.tool_calls):
            return "skill_handler"
            
        return "tools"

    # Add Edges
    workflow.add_conditional_edges("agent", should_continue, ["skill_handler", "tools", END])
    workflow.add_edge("skill_handler", "agent")
    workflow.add_edge("tools", "agent")

    return workflow.compile()
