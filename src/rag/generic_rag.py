import os
from typing import Annotated, TypedDict, List, Union
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from src.rag.data_ingestion import DataIngestion

load_dotenv()

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")  # Asegúrate de configurar tu API KEY en el entorno o aquí directamente para pruebas.

class AgentState(TypedDict):
    """Estado del agente para LangGraph."""
    messages: Annotated[List[BaseMessage], add_messages]


from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import os

# class CustomQdrantVectorStore(QdrantVectorStore):
#     def __init__(self, persist_path: str, collection_name: str, embedding_model):
#         self.persist_path = persist_path
#         self.collection_name = collection_name
        
#         # 1. Creamos el cliente en una variable local para no chocar con self.client
#         client_instance = QdrantClient(path=self.persist_path)
        
#         # 2. Asegurar que la colección exista (usando la instancia local)
#         try:
#             client_instance.get_collection(self.collection_name)
#         except Exception:
#             print(f"📦 Creando nueva colección: {self.collection_name}")
#             client_instance.create_collection(
#                 collection_name=self.collection_name,
#                 vectors_config=VectorParams(size=768, distance=Distance.COSINE),
#             )
        
#         # 3. Inicializar la clase base
#         # LangChain guardará el cliente y el embedding internamente.
#         super().__init__(
#             client=client_instance,
#             collection_name=self.collection_name,
#             embedding=embedding_model
#         )
        
#     def _ensure_collection_exists(self):
#         try:
#             self.client.get_collection(self.collection_name)
#         except Exception:
#             print(f"📦 Creando nueva colección: {self.collection_name}")
#             self.client.create_collection(
#                 collection_name=self.collection_name,
#                 vectors_config=VectorParams(size=768, distance=Distance.COSINE),
#             )

#     def clear_all_data(self):
#         """Limpia la colección de forma segura"""
#         self.client.delete_collection(self.collection_name)
#         self._ensure_collection_exists()
#         print("🗑️ Base de datos vectorial reiniciada.")

#     def close(self):
#         """Cierra la conexión con el almacenamiento local de forma limpia."""
#         if hasattr(self, "client") and self.client:
#             self.client.close()
#             print("🔒 Conexión con Qdrant cerrada exitosamente.")

class CustomQdrantVectorStore(QdrantVectorStore):
    def __init__(self, persist_path: str, collection_name: str, embedding_model):
        self.persist_path = persist_path
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        
        # 1. Intentar crear el cliente
        client_instance = QdrantClient(path=self.persist_path)
        
        # 2. Asegurar colección con dimensiones dinámicas
        self._check_or_create_collection(client_instance)
        
        # 3. Inicializar base de LangChain
        super().__init__(
            client=client_instance,
            collection_name=self.collection_name,
            embedding=self.embedding_model
        )
        
    def _check_or_create_collection(self, client: QdrantClient):
        """Verifica o crea la colección detectando el tamaño del embedding."""
        try:
            client.get_collection(self.collection_name)
        except Exception:
            # Obtenemos la dimensión del modelo de embedding automáticamente
            sample_vector = self.embedding_model.embed_query("test")
            vector_size = len(sample_vector)
            
            print(f"📦 Creando colección: {self.collection_name} (Dimensión: {vector_size})")
            client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    def clear_all_data(self):
        """Limpia la colección de forma segura."""
        self.client.delete_collection(self.collection_name)
        self._check_or_create_collection(self.client)
        print("🗑️ Base de datos vectorial reiniciada.")

    def close(self):
        """Cierra la conexión de forma limpia."""
        if hasattr(self, "client") and self.client:
            # Importante: Acceder al cliente interno de la librería si es necesario
            self.client.close()
            print("🔒 Conexión con Qdrant cerrada exitosamente.")


class RAGSolution:
    def __init__(self, store: CustomQdrantVectorStore, model, embeddings):
            # 1. Modelos
            self.llm = model  # El modelo que definiste globalmente
            self.embeddings = embeddings # Los embeddings definidos globalmente
            
            # 2. Inyección del Vector Store
            self.vector_store = store
            self.client = store.client # Por si necesitas acceso directo al cliente
            
            # 3. Inicializar ingestor
            self.ingestor = DataIngestion(self.embeddings)       
    
    def ingest_data(self, use_clean=True, use_markdown=False):
        """Método público para cargar datos del scraper a la base vectorial"""
        return self.ingestor.ingest_to_vectorstore(
            data_dir_clean="data/celsia_knowledge_base_clean",
            data_dir_markdown="data/celsia_knowledge_base_markdown",
            vector_store=self.vector_store,
            use_clean=use_clean,
            use_markdown=use_markdown
        )
    
    def clear_collection(self):
        """Limpia la colección para reiniciar datos (útil en desarrollo)"""
        try:
            self.client.delete_collection(self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            print("🗑️ Colección limpiada y recreada")
        except Exception as e:
            print(f"❌ Error limpiando colección: {e}")
    
    def get_tools(self):
        @tool
        def retrieve_company_info(query: str):
            """Consulta la base de conocimientos oficial de la empresa para responder preguntas 
            sobre servicios, historia, sedes, horarios y procesos."""
            docs = self.vector_store.similarity_search(query, k=4)
            context = "\n\n".join([f"Fragmento: {d.page_content}" for d in docs])
            return context
        
        return [retrieve_company_info]

    def build_graph(self):
        tools = self.get_tools()
        tool_node = ToolNode(tools)
        model_with_tools = self.llm.bind_tools(tools)

        def call_model(state: AgentState):
            system_prompt = (
                "Eres un asistente experto de la empresa líder del Valle del Cauca. "
                "Tu objetivo es dar respuestas precisas basadas ÚNICAMENTE en la información recuperada. "
                "Si la información no está en el contexto, indica amablemente que no posees ese dato específico. "
                "Responde siempre en español y mantén un tono profesional y servicial."
            )
            messages = [{"role": "system", "content": system_prompt}] + state["messages"]
            response = model_with_tools.invoke(messages)
            return {"messages": [response]}

        def router(state: AgentState):
            last_message = state["messages"][-1]
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            return END

        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", router, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)







