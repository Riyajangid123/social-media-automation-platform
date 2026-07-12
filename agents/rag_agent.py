from rag.retriever import Retriever
from graph.state import GraphState

class RagAgent:

    def __init__(self):
        self.retriever = Retriever()

    def retrieve(self, state: GraphState):
        query = state["user_query"]

        docs = self.retriever.retrieve_docs(query)  
        print(f"RAG found {len(docs)} relevant docs")

        return {"rag_docs": docs}