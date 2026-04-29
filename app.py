import streamlit as st
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from tavily import TavilyClient
import os
import requests

# 1. Funciones de utilidad (Ollama y Tavily)
def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        return [model["name"] for model in response.json()["models"]] if response.status_code == 200 else []
    except:
        return []

def buscar_en_web(query, api_key):
    try:
        tavily = TavilyClient(api_key=api_key)
        respuesta = tavily.search(query=f"Celsia Colombia {query}", search_depth="advanced")
        contexto = "\n\n--- INFO WEB RECIENTE ---\n"
        for res in respuesta['results']:
            contexto += f"- {res['content']} (Fuente: {res['url']})\n"
        return contexto
    except Exception as e:
        return f"\n(Error Web: {e})\n"

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Celsia AI Expert", page_icon="⚡", layout="wide")

with st.sidebar:
    st.title("🚀 Configuración Avanzada")
    
    # A. Selección de IA
    tipo_modelo = st.selectbox("Proveedor", ["Local (Ollama)", "Online (Gemini)"])
    
    # B. Parámetros de Generación (Sliders)
    st.subheader("🎛️ Parámetros de la IA")
    
    temperatura = st.slider(
        "Temperatura", 0.0, 1.0, 0.0, 0.1,
        help="Controla la aleatoriedad: 0 es preciso, 1 es creativo."
    )
    
    top_p = st.slider(
        "Top P (Nucleus Sampling)", 0.0, 1.0, 0.9, 0.1,
        help="Controla la diversidad: valores bajos filtran palabras poco probables."
    )
    
    st.divider()

    # C. Búsqueda Web
    usar_tavily = st.toggle("🔍 Usar Tavily (Web Search)")
    tavily_key = st.text_input("Tavily API Key", type="password") if usar_tavily else None

    # D. Detalles del Modelo
    st.divider()
    if tipo_modelo == "Local (Ollama)":
        modelos = get_ollama_models()
        nombre_modelo = st.selectbox("Modelo Local", modelos) if modelos else st.text_input("Modelo", "gemma")
    else:
        google_key = st.text_input("Google API Key", type="password")
        nombre_modelo = st.selectbox("Versión Gemini", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-3-flash-preview"])

    st.divider()
    prompt_sys = st.text_area("System Prompt", value="Eres el experto de Celsia. Responde usando los datos proporcionados.")


# --- LÓGICA DEL CHAT ---
st.title("⚡ Celsia Intel Assistant")
st.info(f"Modelo: {nombre_modelo} | Temp: {temperatura} | Top-P: {top_p}")

# Carga de archivos locales
@st.cache_data
def load_local_data():
    for f in ["master_context_text.txt"]:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as file: return file.read()
    return "Sin base local."

contexto_local = load_local_data()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if user_input := st.chat_input("¿Qué deseas consultar sobre Celsia?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            
            # Obtener datos de Tavily si aplica
            contexto_web = buscar_en_web(user_input, tavily_key) if usar_tavily and tavily_key else ""
            
            # Unir todo
            prompt_completo = f"{prompt_sys}\n\nCONTEXTO LOCAL:\n{contexto_local}\n\n{contexto_web}"
            
            try:
                # Configurar LLM con Temperatura y Top_P
                if tipo_modelo == "Local (Ollama)":
                    llm = ChatOllama(
                        model=nombre_modelo, 
                        temperature=temperatura,
                        top_p=top_p  # Parámetro aplicado
                    )
                else:
                    llm = ChatGoogleGenerativeAI(
                        model=nombre_modelo, 
                        google_api_key=google_key, 
                        temperature=temperatura,
                        top_p=top_p  # Parámetro aplicado

                    )
                
                msgs = [SystemMessage(content=prompt_completo)]
                for m in st.session_state.messages[-3:]:
                    msgs.append(HumanMessage(content=m["content"]) if m["role"]=="user" else AIMessage(content=m["content"]))
                
            #     res = llm.invoke(msgs)
            #     st.markdown(res.content)
            #     st.session_state.messages.append({"role": "assistant", "content": res.content})
                
            # except Exception as e:
            #     st.error(f"Error: {e}")
                res = llm.invoke(msgs)
                    
                    # --- NUEVA LÓGICA DE LIMPIEZA ---
                respuesta_final = ""
                    
                # Si res.content es una lista, extraemos el campo 'text'
                if isinstance(res.content, list):
                     # Unimos todos los fragmentos de texto por si Gemini devuelve varios
                    respuesta_final = "".join([part.get('text', '') for part in res.content if isinstance(part, dict)])
                else:
                        # Si ya es un string, lo dejamos como está
                    respuesta_final = res.content
                    # -------------------------------

                    st.markdown(respuesta_final)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta_final})
                    
            except Exception as e:
                st.error(f"Error: {e}")