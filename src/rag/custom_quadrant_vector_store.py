from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


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
