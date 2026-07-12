from langchain_text_splitters import RecursiveCharacterTextSplitter
from rag.loader import Loader

class Text_Splitter:
    def Split(self):
        docs=Loader().doc_loader()

        splitter=RecursiveCharacterTextSplitter(chunk_size=300,chunk_overlap=50)

        chunks=splitter.split_documents(docs)
        print(f"Total chunks: {len(chunks)}")

        return chunks
        