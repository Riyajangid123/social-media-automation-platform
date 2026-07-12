from rag.embedding import Embedding

class Retriever:
    def retrieve_docs(self,query:str):
        vector=Embedding().load_embeddings()

        retriever=vector.as_retriever(search_kwargs={"k":3})

        docs=retriever.invoke(query)

        return [doc.page_content for doc in docs]