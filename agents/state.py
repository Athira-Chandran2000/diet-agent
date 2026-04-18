from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    next_agent: str
    user_intent: str
    context: dict