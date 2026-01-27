import operator
from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """The state of the agent, containing conversation history and active skills."""
    messages: Annotated[List[BaseMessage], operator.add]
    active_skills: str
