from langchain_community.document_loaders import DirectoryLoader,TextLoader

class Loader:
    def doc_loader(self):
        loader=DirectoryLoader("docs",glob="**/*.txt",loader_cls=TextLoader)

        docs=loader.load()

        print(f"Loaded {len(docs)} documents")

        return docs


        
