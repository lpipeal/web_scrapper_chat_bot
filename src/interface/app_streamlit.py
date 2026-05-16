import ollama
import streamlit as st
from run_batch import get_agent_app
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# --- FUNCIONES DE UX Y GESTIÓN DE SESIONES ---
def create_new_session():
    new_id = str(uuid.uuid4())
    numero_chat = len(st.session_state.chat_sessions) + 1
    st.session_state.chat_sessions[new_id] = {
        "name": f"Consulta #{numero_chat}", 
        "history": []
    }
    st.session_state.current_session = new_id

def send_faq(question):
    st.session_state.faq_trigger = question

def main():
    st.set_page_config(page_title="Asistente Corporativo Celsia ⚡", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
    
    st.markdown("""
        <style>
            #MainMenu {visibility: hidden;}
            .stChatMessage { border-radius: 16px !important; padding: 18px !important; margin-bottom: 20px !important; box-shadow: 0 4px 12px rgba(0,0,0,0.06) !important;}
            [data-testid="chatAvatarIcon-user"] { background-color: #F37021 !important; }
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) { background-color: #FFFFFF !important; border: 1px solid #DCDCDC !important;}
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color: #2B2B2B !important; }
            [data-testid="chatAvatarIcon-assistant"] { background-color: #2B2B2B !important; }
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) { background-color: #F5F5F5 !important; border: 1px solid #E0E0E0 !important;}
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) p,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) li,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) span,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) strong,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) h1,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) h2,
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) h3 { color: #2B2B2B !important; font-weight: 500 !important;}
            div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) a { color: #F37021 !important; text-decoration: underline !important;}
            .stButton>button { border: 1px solid #2B2B2B !important; color: #2B2B2B !important; background-color: #FFFFFF !important; border-radius: 20px !important; transition: all 0.3s ease; font-weight: 600 !important;}
            .stButton>button:hover { background-color: #F37021 !important; color: #FFFFFF !important; border: 1px solid #F37021 !important;}
            [data-testid="stSidebar"] .stExpander { background-color: #F5F5F5 !important; border: 1px solid #D6560F !important; border-radius: 12px !important; margin-top: 15px !important;}
            [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] .stExpander p { color: #2B2B2B !important; font-weight: 600 !important;}
            [data-testid="stSidebar"] .stExpander svg { fill: #2B2B2B !important;}
        </style>
    """, unsafe_allow_html=True)

    if "chat_sessions" not in st.session_state:
        default_id = str(uuid.uuid4())
        st.session_state.chat_sessions = {default_id: {"name": "Chat Principal", "history": []}}
        st.session_state.current_session = default_id
    
    current_thread_id = st.session_state.current_session
    current_history = st.session_state.chat_sessions[current_thread_id]["history"]

    with st.sidebar:
        try:
            st.image("logo_celsia.png", use_container_width=True)
        except Exception:
            st.markdown("<h2 style='color: #2B2B2B; text-align: center;'>⚡ CELSIA</h2>", unsafe_allow_html=True)
        
        st.markdown("### 🗂️ Tus Conversaciones")
        if st.button("➕ Nuevo Chat", use_container_width=True):
            create_new_session()
            st.rerun()

        session_options = {k: v["name"] for k, v in st.session_state.chat_sessions.items()}
        selected_session = st.radio("Historial:", options=list(session_options.keys()), format_func=lambda x: session_options[x], label_visibility="collapsed")
        
        if selected_session != st.session_state.current_session:
            st.session_state.current_session = selected_session
            st.rerun()

        session_id = st.session_state.current_session
        nombre_actual = st.session_state.chat_sessions[session_id]["name"]
        nuevo_nombre = st.text_input("✏️ Renombrar chat actual:", value=nombre_actual, key=f"rename_{session_id}")
        
        if nuevo_nombre and nuevo_nombre != nombre_actual:
            st.session_state.chat_sessions[session_id]["name"] = nuevo_nombre
            st.rerun() 

        st.markdown("---")
        with st.expander("⚙️ Configuración del Agente"):
            proveedor = st.selectbox("Proveedor", ["Local (Ollama)", "En línea (Gemini)"])
            if proveedor == "En línea (Gemini)":
                modelos_disponibles = ["Gemini Flash Latest", "Gemini Pro Latest", "Gemini 3.1 Flash Lite", "Gemini 3 Flash Preview", "Gemini 3.1 Pro Preview", "Gemini Flash-Lite Latest"]
                selected_model = st.selectbox("Modelo en línea", modelos_disponibles)
            else:
                try:

                    # Fetch model list from Ollama
                    models_info = ollama.list()

                    # 1. Extract model names (safe for both object and dict responses)
                    all_models = [m.model for m in models_info.models] if hasattr(models_info, 'models') else [m['name'] for m in models_info.get('models', [])]

                    # 2. Filter out embeddings: remove any name containing "embed"
                    available_models = [m for m in all_models if "embed" not in m.lower()]

                    # 3. Set preferred model
                    PREFERRED_MODEL = "mistral"

                    # 4. Find preferred model (exact match or with :latest tag)
                    active_model = next(
                        (m for m in available_models if m == PREFERRED_MODEL or m == f"{PREFERRED_MODEL}:latest"),
                        None
                    )

                    # 5. Fallback if preferred model is not downloaded
                    if active_model is None:
                        if available_models:
                            active_model = available_models[0]
                            print(f"⚠️ '{PREFERRED_MODEL}' not found. Using fallback: {active_model}")
                        else:
                            raise RuntimeError("❌ No LLM models downloaded in Ollama")
                        
                    modelos_disponibles = available_models

                    default_idx = available_models.index(active_model) if active_model in available_models else 0

                    selected_model = st.selectbox(
                        "Modelo local:", 
                        modelos_disponibles, 
                        index=default_idx,
                        key="selected_ollama_model"  # Mantiene la selección entre reruns
                    )

                except:
                    modelos_disponibles = ["Error al conectar con Ollama"]
                    selected_model = st.selectbox("Modelo local:", modelos_disponibles)

            temperature = st.slider("Temperatura", 0.0, 1.0, 0.1, 0.1)
            valor_p = st.slider(
                "Valor P (Top-p Nucleus Sampling)",
                min_value=0.0,
                max_value=1.0,
                value=0.9,  # Valor por defecto recomendado
                step=0.05,
                help="Controla la diversidad de la respuesta vía muestreo de núcleo. 1.0 significa que se consideran todos los tokens."
            )
            k_conocimientos = st.number_input("Docs a recuperar", min_value=1, max_value=10, value=6)
            
            if st.button("Limpiar Historial Actual", use_container_width=True):
                st.session_state.chat_sessions[st.session_state.current_session]["history"] = []
                st.rerun()

        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.divider()
        st.caption(f"⚡ Powered by LangChain | LangGraph | Qdrant | Thread: `{current_thread_id[:8]}...`")

    st.title("⚡ Asistente Inteligente Celsia")
    st.caption("Arquitectura RAG Avanzada con LangGraph & Qdrant")

    if not current_history:
        st.markdown("#### ¿En qué te puedo asesorar hoy?")
        col1, col2, col3 = st.columns(3)
        with col1: st.button("📄 Detalles de mi factura", on_click=send_faq, args=("¿Cómo entiendo mi factura de energía?",), use_container_width=True)
        with col2: st.button("💰 Temas de subsidios", on_click=send_faq, args=("¿Cómo funcionan los subsidios de energía?",), use_container_width=True)
        with col3: st.button("🔌 Reportar interrupción", on_click=send_faq, args=("¿Qué hago si no tengo servicio de energía?",), use_container_width=True)
        st.markdown("---")

    for msg in current_history:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        avatar = "👤" if role == "user" else "⚡"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg.content)

    prompt = st.chat_input("¿En qué puedo ayudarte hoy?")
    if "faq_trigger" in st.session_state:
        prompt = st.session_state.faq_trigger
        del st.session_state.faq_trigger

    if prompt:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # 1. Agregamos el mensaje del usuario a la memoria VISUAL y GLOBAL
        user_msg = HumanMessage(content=prompt)
        st.session_state.chat_sessions[current_thread_id]["history"].append(user_msg)

        with st.chat_message("assistant", avatar="⚡"):
            with st.spinner("Consultando con Celsia..."):
                
                # 2. Generamos la app y abrimos base de datos vectorial
                app_graph, rag_engine, context = get_agent_app(
                    proveedor=proveedor, 
                    model_choice=selected_model, 
                    temperature=temperature, 
                    k_docs=k_conocimientos,
                    valor_p=valor_p
                )
                
                config = {"configurable": {"thread_id": current_thread_id}}

                try:
                    # 3. 🧠 LA CURA A LA AMNESIA: Enviamos el current_history COMPLETO
                    final_state = app_graph.invoke(
                        {
                            "query": prompt, 
                            "messages": current_history, # <-- ¡Enviamos TODA la memoria!
                            "context_data": "",
                            "route": ""
                        },
                        config=config
                    )
                    
                    response_text = final_state.get("final_answer", "No pude procesar una respuesta.")
                    st.markdown(response_text)
                    
                    # 4. Guardamos la respuesta del LLM
                    st.session_state.chat_sessions[current_thread_id]["history"].append(AIMessage(content=response_text))

                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        st.error("⚠️ **Límite de cuota alcanzado.** El proveedor del modelo ha agotado sus peticiones gratuitas por hoy.")
                    else:
                        st.error(f"⚠️ **Error de comunicación con el LLM:** {error_msg}")
                    st.stop()
                finally:
                    # 5. 🔒 LA CURA AL BLOQUEO DE QDRANT: Cerramos explícitamente el motor RAG
                    rag_engine.close()

if __name__ == "__main__":
    main()