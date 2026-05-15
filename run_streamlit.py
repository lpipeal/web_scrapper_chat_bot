# === 🟢 PRIMERO: Cargar variables de entorno ===
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

# Cargar .env desde la raíz del proyecto
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Verificar API Key (opcional pero útil para debug)
if not os.getenv("GOOGLE_API_KEY"):
    st.error("❌ GOOGLE_API_KEY no configurada. Revisa tu archivo .env")
    st.stop()

# Agregar la raíz del proyecto al PYTHONPATH para imports relativos
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# === 🟢 AHORA sí, importar el resto ===
import streamlit as st
# from backend_agent import app_graph
# from langchain_core.messages import HumanMessage, AIMessage
# import uuid

from src.interface.app_streamlit import main

if __name__ == "__main__":
    main()