from rag.embedding import Embedding

if __name__=="__main__":
    generate_emb=Embedding().generate_embedding()
    print("RAG DB ready!")