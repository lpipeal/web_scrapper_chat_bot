# 1. Estado del Grafo
from typing import Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from litellm import TypedDict

class CelsiaAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    route: str            # La decisión del router
    context_data: str     # Los datos extraídos (del JSON o de Qdrant)
    final_answer: str     # La respuesta final en lenguaje natural