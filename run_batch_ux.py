import asyncio
import os
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from src.rag.custom_quadrant_vector_store import CustomQdrantVectorStore 
from src.context.agent_context import AgentContext
from src.rag.rag_solution import RAGSolution
from src.graph_solution.graph_factory import CelsiaWorkflow
from src.web_scraper.web_scrapper import web_scraping_init

def get_agent_app(proveedor="Local (Ollama)", model_choice="mistral:latest", temperature=0.1, k_docs=6, valor_p=0.9):
    PERSIST_PATH = "data/vectorial_database/qdrant_storage"
    COLLECTION_NAME = "celsia_knowledge_base"
    
    # 1. Selección dinámica del LLM (Local vs Nube)
    if proveedor == "En línea (Gemini)":
        gemini_model_map = {
            "Gemini Flash Latest": "models/gemini-flash-latest",
            "Gemini Pro Latest": "models/gemini-pro-latest",
            "Gemini 3.1 Flash Lite": "models/gemini-3.1-flash-lite", 
            "Gemini 3 Flash Preview": "models/gemini-3-flash-preview",
            "Gemini 3.1 Pro Preview": "models/gemini-3.1-pro-preview",
            "Gemini Flash-Lite Latest": "models/gemini-flash-lite-latest"
        }
        api_model_string = gemini_model_map.get(model_choice, "models/gemini-flash-lite-latest")
        print(f"DEBUG: Nombre en UI: '{model_choice}' -> Enviando a API: '{api_model_string}'")
        
        llm = ChatGoogleGenerativeAI(model=api_model_string, temperature=temperature, top_p=valor_p)
    else:
        llm = ChatOllama(model=model_choice, temperature=temperature, top_p=valor_p)
        
    embeddings = OllamaEmbeddings(model="nomic-embed-text-v2-moe:latest")
    
    # 2. Crear el almacén (Se abre conexión a Qdrant)
    vector_store = CustomQdrantVectorStore(
        persist_path=PERSIST_PATH,
        collection_name=COLLECTION_NAME,
        embedding_model=embeddings 
    )
    
    # 3. Contexto
    context = AgentContext(
        llm=llm, 
        embeddings=embeddings, 
        vector_store=vector_store, 
        basic_info_path="data/documents/basic_information.json",
        k_docs=k_docs,  
    )
    # Inyectamos k_docs por si AgentContext no lo recibe en su __init__
    # context.k_docs = k_docs
    # context.valor_p = valor_p

    rag_engine = RAGSolution(context)
    app_graph = CelsiaWorkflow(context).build()
    
    return app_graph, rag_engine, context

# ⚠️ ELIMINADA LA INSTANCIACIÓN GLOBAL AQUÍ PARA EVITAR EL BLOQUEO DE QDRANT

async def main():
    # Solo para pruebas locales por consola
    try:
        app_graph, rag_engine, context = get_agent_app()
        print("\n🤖 Bot de Celsia Online. Haz tu pregunta:")
        query = "¿Cuál es el NIT y qué servicios tienen para empresas?"
        
        from langchain_core.messages import HumanMessage
        config = {"configurable": {"thread_id": "sesion_probar_rag"}}
        
        result = await app_graph.ainvoke(
            {
                "query": query, 
                "messages": [HumanMessage(content=query)], 
                "context_data": "", 
                "route": ""
            },
            config=config
        )
        print(f"\n--- RESPUESTA ---\n{result['final_answer']}")

    finally:
        # Aquí se libera la base de datos al usar consola
        rag_engine.close()

if __name__ == "__main__":
    asyncio.run(main())