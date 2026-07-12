from langchain_community.vectorstores import Chroma
from rag.chunking import Text_Splitter
from langchain_huggingface import HuggingFaceEmbeddings

class Embedding:
    def generate_embedding(self):
        chunks=Text_Splitter().Split()

        embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store=Chroma.from_documents(chunks,embeddings,persist_directory="./rag_db")

        print("RAG database built successfully!")
        return vector_store
    
    def load_embeddings(self):
        embeddings=HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store=Chroma(
            persist_directory="./rag_db",
            embedding_function=embeddings
        )

        return vector_store

