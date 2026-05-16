import streamlit as st
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from run_batch import app_graph

def main():
    # --- CONFIGURACIÓN DE PÁGINA ---
    st.set_page_config(
        page_title="Asistente Corporativo Celsia",
        page_icon="🤖",
        layout="centered"
    )

    # Estilo personalizado
    st.markdown("""
        <style>
        .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
        .main { background-color: #f8f9fa; }
        h1 { color: #1E3A8A; font-family: 'Helvetica'; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🤖 Asistente Inteligente Celsia")
    st.caption("Arquitectura con Memoria de Corto Plazo (LangGraph + Checkpointer)")

    # --- GESTIÓN DE ESTADO (MEMORIA) ---
    # El thread_id es la "llave" de la memoria en la base de datos/checkpointer
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    # Historial para mostrar en la UI de Streamlit
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("Panel de Control")
        st.write(f"**Sesión ID:** `{st.session_state.thread_id}`")
        
        if st.button("🗑️ Nueva Conversación"):
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()

    # --- CHAT INTERFACE ---
    # Renderizar historial
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Entrada del usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
        # 1. Crear el mensaje de humano
        user_msg = HumanMessage(content=prompt)
        
        # 2. Mostrarlo inmediatamente en la UI
        st.session_state.messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(prompt)

        # 3. Generación con el Grafo
        with st.chat_message("assistant"):
            with st.spinner("Razonando con memoria..."):
                # Configuración necesaria para que el Checkpointer sepa qué hilo recuperar
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                # Invocación enviando el mensaje en la lista 'messages'
                # IMPORTANTE: Enviamos el objeto mensaje, no solo el string
                final_state = app_graph.invoke(
                    {
                        "query": prompt, 
                        "messages": [user_msg], # add_messages lo unirá al historial previo
                        "context_data": "",
                        "route": ""
                    },
                    config=config
                )
                
                # 4. Extraer respuesta
                response_text = final_state.get("final_answer", "No pude procesar una respuesta.")
                st.markdown(response_text)
                
                # 5. Guardar respuesta del asistente en el historial de la UI
                st.session_state.messages.append(AIMessage(content=response_text))

    st.divider()
    st.caption("Celsia Agent | LangGraph Memory Enabled")