from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import streamlit as st
import os

# 1. Configuración de la Interfaz
st.set_page_config(page_title="Celsia AI Assistant", page_icon="⚡", layout="wide")

# ESTILOS CORREGIDOS
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    </style>
    """, unsafe_allow_html=True) 

st.title("⚡ Celsia Knowledge Assistant")
st.subheader("Consulta información oficial sobre la red, trámites y sostenibilidad.")

# 2. Cargar el Contexto Consolidado
# Asegúrate de que el archivo 'master_context_clean.txt' contenga todo lo que me mostraste
@st.cache_data
def load_full_context():
    if os.path.exists("master_context.txt"):
        with open("master_context.txt", "r", encoding="utf-8") as f:
            return f.read()
    return "No se encontró la base de conocimientos."

contexto_completo = load_full_context()

# 3. Inicializar el Modelo Ollama
# Ajustamos num_ctx para aprovechar tu ventana de tokens
llm = ChatOllama(
    # model="gemma4:e4b", # Asegúrate de que este sea el nombre exacto en 'ollama list'
    model="mistral", # O cambia a "llama3" o "mistral" si prefieres
    temperature=0,
    num_ctx=4096, # Aunque tengas 128k, 32k suele ser más que suficiente y más rápido
)

# 4. Prompt Engineering (El Cerebro)
prompt_sistema = f"""
Eres el Asistente Virtual Inteligente de Celsia (empresa del Grupo Argos). 
Tu misión es resolver dudas de usuarios basándote EXCLUSIVAMENTE en el contexto proporcionado.

INSTRUCCIONES DE COMPORTAMIENTO:
1. Usa el contexto para responder sobre: Pagos, facturas digitales, trámites de autogeneración, subestaciones (Estambul y Las Palmas), y servicios Pymes.
2. Si el usuario pregunta algo que NO está en el texto (ej. "precio del dólar"), responde: 
   "Lo siento, como asistente de Celsia solo puedo ayudarte con información relacionada a nuestros servicios de energía e internet. Para ese dato, te sugiero consultar fuentes externas."
3. Si mencionas las subestaciones de Palmira, destaca la inversión de $130 mil millones.
4. Mantén un tono corporativo pero amable.

CONTEXTO DE CELSIA:
{contexto_completo}
"""

# 5. Historial de Chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostrar mensajes previos
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Lógica de Interacción
if user_input := st.chat_input("Escribe tu pregunta sobre Celsia aquí..."):
    # Agregar pregunta del usuario
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generar respuesta de la IA
    with st.chat_message("assistant"):
        with st.spinner("Buscando en la base de conocimientos de Celsia..."):
            try:
                # Construimos la estructura de mensajes para LangChain
                messages = [
                    SystemMessage(content=prompt_sistema),
                    HumanMessage(content=user_input)
                ]
                
                # Invocación al modelo local
                response = llm.invoke(messages)
                full_response = response.content
                
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                st.error(f"Hubo un error con Ollama: {e}")
                st.info("Asegúrate de tener Ollama corriendo en segundo plano (`ollama serve`).")