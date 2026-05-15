import streamlit as st
from run_batch import app_graph
from langchain_core.messages import HumanMessage, AIMessage
import uuid

def main():
    # --- CONFIGURACIÓN DE PÁGINA ---
    st.set_page_config(
        page_title="Asistente Corporativo Valle del Cauca",
        page_icon="🤖",
        layout="centered"
    )

    # Estilo personalizado para un look "bonito"
    st.markdown("""
        <style>
        .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
        .main { background-color: #f8f9fa; }
        h1 { color: #1E3A8A; font-family: 'Helvetica'; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🤖 Asistente Inteligente Corporativo")
    st.caption("Arquitectura RAG Avanzada con LangGraph & Gemini")

    # --- GESTIÓN DE ESTADO (MEMORIA) ---
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- SIDEBAR - PANEL DE CONTROL ---
    with st.sidebar:
        st.header("Configuración")
        st.info("Este agente utiliza memoria de corto plazo y un router lógico para decidir cuándo consultar la base de datos Qdrant.")
        if st.button("Limpiar Historial"):
            st.session_state.messages = []
            st.session_state.thread_id = str(uuid.uuid4())
            st.rerun()

    # --- CHAT INTERFACE ---
    # Mostrar mensajes anteriores
    for msg in st.session_state.messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        with st.chat_message(role):
            st.markdown(msg.content)

    # Entrada del usuario
    if prompt := st.chat_input("¿En qué puedo ayudarte hoy?"):
        # Guardar y mostrar mensaje del usuario
        user_msg = HumanMessage(content=prompt)
        st.session_state.messages.append(user_msg)
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generación de respuesta con Spinner
        with st.chat_message("assistant"):
            with st.spinner("Consultando base de conocimientos y razonando..."):
                config = {"configurable": {"thread_id": st.session_state.thread_id}}
                
                # Ejecutar el grafo de LangGraph
                user_query = st.session_state.messages[-1].content 

                final_state = app_graph.invoke(
                    {
                        "query": user_query,
                        "context_data": "",
                        "route": ""
                    },
                    config=config
                )
                
                # Obtener el último mensaje del estado (la respuesta del AI)
                # response_text = final_state["messages"][-1].content
                # st.markdown(response_text)
                response_text = final_state.get("final_answer", "Lo siento, hubo un error al procesar la respuesta.")
                st.markdown(response_text)
                
                # Guardar respuesta en el historial
                st.session_state.messages.append(AIMessage(content=response_text))

    # Pie de página técnico
    st.divider()
    st.caption("Powered by LangChain | LangGraph | Qdrant | Gemini 1.5 Flash")

if __name__ == "__main__":
    main()