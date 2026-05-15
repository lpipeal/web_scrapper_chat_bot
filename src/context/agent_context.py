import yaml
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate

class AgentContext:
    def __init__(self, llm, embeddings, vector_store, basic_info_path: str):
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.basic_info_path = basic_info_path
        
        # Centralizamos la carga de YAMLs
        self.params = self._load_yaml("src/config/params.yaml")
        self.prompts_config = self._load_yaml("src/config/prompts.yaml").get("prompts", {})

    def _load_yaml(self, path: str) -> Dict:
        """Cargador genérico de archivos YAML."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️ Advertencia: Archivo {path} no encontrado.")
            return {}

    def get_prompt(self, prompt_name: str) -> ChatPromptTemplate:
        """Busca un prompt por nombre y lo convierte a formato LangChain."""
        raw_prompt = self.prompts_config.get(prompt_name)
        if not raw_prompt:
            raise ValueError(f"❌ El prompt '{prompt_name}' no existe en prompts.yaml")
        
        messages = []
        for msg in raw_prompt:
            role = "human" if msg["role"] in ["user", "human"] else msg["role"]
            messages.append((role, msg["content"]))
            
        return ChatPromptTemplate.from_messages(messages)