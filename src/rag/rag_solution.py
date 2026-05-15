from src.rag.data_ingestion import DataIngestion
from src.context.agent_context import AgentContext

class RAGSolution:
    """
    Motor de persistencia y procesamiento de documentos.
    No conoce la lógica del agente, solo gestiona vectores.
    """
    def __init__(self, context: AgentContext):
        self.context = context
        # Usamos el embedding centralizado en el contexto
        self.ingestor = DataIngestion(self.context.embeddings)

    def prepare_knowledge_base(self, re_ingest: bool = False):
        """Prepara la base de datos vectorial si es necesario."""
        if re_ingest:
            print("🗑️ Vaciando base de datos vectorial...")
            self.context.vector_store.clear_all_data()
            
            print("🚀 Iniciando ingestión de nuevos documentos...")
            num_docs = self.ingestor.ingest_to_vectorstore(
                data_dir_clean=self.context.params["paths"]["clean_data"],
                data_dir_markdown=self.context.params["paths"]["markdown_data"],
                vector_store=self.context.vector_store,
                use_clean=True,
                use_markdown=False
            )
            print(f"🎉 Ingestión terminada: {num_docs} fragmentos guardados.")
            return num_docs
        return 0

    def close(self):
        """Cierra conexiones de base de datos."""
        self.context.vector_store.close()