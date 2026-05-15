import json
from langgraph.graph import StateGraph, START, END
from src.context.agent_context import AgentContext
from src.graph_solution.state import CelsiaAgentState


# --- NODOS COMO CLASES ---
class RouterNode:
    def __init__(self, context: AgentContext):
        self.context = context
        self.prompt = context.get_prompt("router_prompt")

    def __call__(self, state: CelsiaAgentState):
        user_input = state.get("query")
    
        if not user_input and "messages" in state:
            user_input = state["messages"][-1].content

        print(f"DEBUG: Buscando en {self.context.basic_info_path}")
        chain = self.prompt | self.context.llm
        result = chain.invoke({"query": user_input})
        try:
            # Limpieza básica de respuesta JSON
            clean_json = result.content.strip().replace("```json", "").replace("```", "")
            route = json.loads(clean_json).get("route", "RAG_SEARCH")
        except: route = "RAG_SEARCH"
        return {"route": route}

class BasicInfoNode:
    def __init__(self, context: AgentContext):
        self.context = context

    def __call__(self, state: CelsiaAgentState):
        print(f"DEBUG: Cargando información básica desde {self.context.basic_info_path}")
        with open(self.context.basic_info_path, "r", encoding="utf-8") as f:
            data = f.read()
        print(f"DEBUG: Información básica cargada: {data}")
        return {"context_data": f"INFORMACIÓN BÁSICA: {data}"}

class RAGSearchNode:
    def __init__(self, context: AgentContext):
        self.context = context

    def __call__(self, state: CelsiaAgentState):
        print(f"DEBUG: Buscando en el vector store con query: {state['query']}")
        docs = self.context.vector_store.similarity_search(state["query"], k=6)
        context_str = "\n\n".join([d.page_content for d in docs])
        print(f"DEBUG: Contexto encontrado: {context_str}")
        return {"context_data": context_str}

class GeneratorNode:
    def __init__(self, context: AgentContext):
        self.context = context
        self.prompt = context.get_prompt("generator_prompt")

    def __call__(self, state: CelsiaAgentState):
        print(f"DEBUG: Generando respuesta con contexto: {state['context_data']}")
        chain = self.prompt | self.context.llm
        result = chain.invoke({"query": state["query"], "context_data": state["context_data"]})
        return {"final_answer": result.content}


from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

class CelsiaWorkflow:
    def __init__(self, context: AgentContext):
        self.context = context

    def _route_logic(self, state: CelsiaAgentState) -> str:
        """Lógica de enrutamiento con normalización y manejo de errores."""
        # Extraemos la ruta, la pasamos a minúsculas y quitamos espacios
        route = state.get("route", "rag_search").lower().strip()
        
        # Mapa de validación para asegurar que solo devolvemos rutas existentes
        # Si el modelo dice 'direct_answer', lo mandamos al generador directamente
        mapping = {
            "basic_info": "basic_info",
            "rag_search": "rag_search",
            "direct_answer": "generator" 
        }
        
        # Si la ruta no está en el mapa, usamos 'rag_search' como fallback seguro
        return mapping.get(route, "rag_search")

    def build(self):
        print(f"DEBUG: Construyendo el flujo de trabajo")
        workflow = StateGraph(CelsiaAgentState)
        
        # 1. Definición de Nodos
        workflow.add_node("router", RouterNode(self.context))
        workflow.add_node("basic_info", BasicInfoNode(self.context))
        workflow.add_node("rag_search", RAGSearchNode(self.context))
        workflow.add_node("generator", GeneratorNode(self.context))

        # 2. Definición de Aristas (Edges)
        workflow.add_edge(START, "router")

        # 3. Aristas Condicionales con soporte para direct_answer
        workflow.add_conditional_edges(
            "router",
            self._route_logic,
            {
                "basic_info": "basic_info",
                "rag_search": "rag_search",
                "generator": "generator" # Esta es la ruta para direct_answer
            }
        )

        # 4. Aristas de convergencia hacia el generador
        workflow.add_edge("basic_info", "generator")
        workflow.add_edge("rag_search", "generator")
        
        # El generador siempre es el final
        workflow.add_edge("generator", END)

        memory = MemorySaver()

        return workflow.compile()    