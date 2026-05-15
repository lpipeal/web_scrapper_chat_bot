import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter, json
from langchain_core.documents import Document
import hashlib
import re
import json

# from pathlib import Path
# from langchain_core.documents import Document

class DataIngestion:
    def __init__(self, embeddings,  chunk_size=500, chunk_overlap=50):
        self.embeddings = embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    def load_clean_files(self, data_dir: str):
        """
        Cargador genérico que utiliza metadata.json para asignar URLs 
        y evita duplicidad mediante hashing de contenido.
        """
        documents = []
        data_path = Path(data_dir)
        metadata_file = data_path / "metadata.json"
        
        # Cargar el mapeo de URLs
        metadata_map = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_map = json.load(f)

        # Set para evitar duplicados de contenido real
        seen_hashes = set()

        for file_path in data_path.glob("*.txt"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if not content:
                continue

            # 1. Crear un Hash del contenido (los primeros 1000 chars suelen bastar)
            # Esto detecta si el texto es idéntico a otro ya procesado
            content_hash = hashlib.md5(content[:1000].encode('utf-8')).hexdigest()
            
            if content_hash in seen_hashes:
                continue # Es un duplicado semántico, lo saltamos
            
            seen_hashes.add(content_hash)

            # 2. Obtener URL real desde la metadata
            # Si el archivo no está en el JSON (raro), intentamos reconstruir o dejar base
            file_info = metadata_map.get(file_path.name, {})
            source_url = file_info.get("url", "https://dominio-desconocido.com")

            # 3. Crear el Documento para LangChain
            metadata = {
                "source": file_path.name,
                "url": source_url,
                "type": "clean"
            }
            
            documents.append(Document(page_content=content, metadata=metadata))

        print(f"📥 Cargados {len(documents)} documentos únicos de {data_dir}")
        return documents

    def load_markdown_files(self, data_dir: str = "data/celsia_knowledge_base_markdown"):
        """Carga archivos markdown (útil como complemento)"""
        documents = []
        md_path = Path(data_dir)
        
        for file_path in md_path.glob("*.md"):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Limpiar sintaxis markdown pero mantener estructura
            content_clean = self._clean_markdown(content)
            
            metadata = {
                "source": file_path.name,
                "type": "markdown",
                "file_path": str(file_path)
            }
            
            doc = Document(page_content=content_clean, metadata=metadata)
            documents.append(doc)
        
        return documents
    
    def _clean_markdown(self, text: str) -> str:
        """Limpia sintaxis markdown pero preserva la estructura semántica"""
        # Remover símbolos markdown pero mantener el texto
        text = re.sub(r'#{1,6}\s*', '', text)  # Headers
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)  # Italic
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links
        text = re.sub(r'<.*?>', '', text)  # HTML tags
        return text.strip()
    
    def create_semantic_chunks(self, documents: list) -> list:
        """
        Crea chunks preservando contexto semántico
        Estrategia: chunking por secciones lógicas
        """
        all_chunks = []
        
        for doc in documents:
            # Dividir por secciones naturales (doble newline o títulos implícitos)
            sections = re.split(r'\n\s*\n|\n(?=[A-Z][a-z]+:)', doc.page_content)
            
            for i, section in enumerate(sections):
                section = section.strip()
                if len(section) > 50:  # Ignorar secciones muy cortas
                    chunk_doc = Document(
                        page_content=section,
                        metadata={
                            **doc.metadata,
                            "chunk_id": i,
                            "section_length": len(section)
                        }
                    )
                    all_chunks.append(chunk_doc)
        
        # Aplicar splitter para chunks muy largos
        final_chunks = self.text_splitter.split_documents(all_chunks)
        final_chunks = self.text_splitter.split_documents(documents)
    
        # Limpieza extra: quitar chunks que son solo "clic aquí" o muy cortos
        return [c for c in final_chunks if len(c.page_content.strip()) > 100]
    
    def ingest_to_vectorstore(self, vector_store, use_clean=True, use_markdown=False, data_dir_clean: str = None, data_dir_markdown: str = "data/celsia_knowledge_base_markdown"):
        """
        Ingesta datos a la base vectorial
        Recomendación: usa clean=True, markdown=False inicialmente
        """
        documents = []
        
        if use_clean:
            print("📂 Cargando archivos limpios...")
            clean_docs = self.load_clean_files(data_dir_clean)
            documents.extend(clean_docs)
            print(f"✓ {len(clean_docs)} archivos limpios cargados")
        
        if use_markdown:
            print("📂 Cargando archivos markdown...")
            md_docs = self.load_markdown_files(data_dir_markdown)
            documents.extend(md_docs)
            print(f"✓ {len(md_docs)} archivos markdown cargados")
        
        print("\n🔄 Creando chunks semánticos...")
        chunks = self.create_semantic_chunks(documents)
        print(f"✓ {len(chunks)} chunks creados")
        print(f"   (Ejemplo chunk 1): {chunks[0].page_content[:200]}...")
        
        print("\n💾 Insertando en base vectorial...")
        vector_store.add_documents(chunks)
        print(f"✓ {len(chunks)} documentos indexados en Qdrant")
        
        return len(chunks)